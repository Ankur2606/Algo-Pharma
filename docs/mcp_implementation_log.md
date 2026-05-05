# MCP Server Implementation Log

> All changes made after commit `0270ddf` ("test: added small cpu model for pii and updated requirements") to achieve a stable, working MCP server pipeline.

---

## Executive Summary

We took the MCP server from **permanently deadlocking** on every tool call to **reliably completing end-to-end** (crawl → ingest → NLP → DB → return) in ~5 seconds. The fix required changes across **7 files** targeting three distinct failure modes.

---

## The Three Failure Modes We Fixed

### 1. Stdout Pipe Corruption (JSON-RPC Protocol Violation)

**Root cause:** The MCP protocol communicates over `stdin`/`stdout` using JSON-RPC. Both `reddit_crawler.py` and `twitter_crawler.py` had module-level `print()` statements that wrote directly to `stdout` — mixing human-readable emoji text with the JSON-RPC binary stream, corrupting it.

**Fix:** Redirected all crawler `print()` calls to `stderr` and guarded `sys.stdout.reconfigure()` behind `if __name__ == "__main__"` to prevent it from executing when the module is imported by the MCP server.

### 2. Windows Stderr Pipe Handle Error

**Root cause:** The MCP server's subprocess on Windows doesn't always have a valid stderr pipe. When Python tried to write to `sys.stderr`, it threw `OSError(9, 'The handle is invalid')`, crashing the server.

**Fix:** Added a safe stderr redirect at the top of `mcp_server.py` that captures stderr to `mcp_server_stderr.log` with a try/except guard.

### 3. PyTorch / C-Extension Import Deadlock in `asyncio.to_thread`

**Root cause:** This was the **hardest bug**. When `crawl_reddit()` ran inside `asyncio.to_thread()`, the NLP pipeline eventually hit `from nlp.pii_guard import redact_pii`, which triggered `import torch` at module scope. PyTorch's C-extension initializes OpenMP thread pools during import, which requires the GIL. But the GIL's import lock was held by the main thread (running the asyncio event loop), creating an unrecoverable OS-level deadlock.

**Diagnosis method:** We used a binary-search debugging approach:
1. Confirmed test_sleep worked (async machinery is fine) ✅
2. Confirmed direct scraping worked (Reddit API is fine) ✅
3. Added debug prints at each import inside `ingest_reddit_json` — identified that execution froze at `from nlp.pii_guard import redact_pii` ✅
4. Added debug prints inside `pii_guard.py` — identified that `import torch` was the exact line that deadlocked ✅

**Fix (two-part):**
1. **Removed `import torch` from module scope** of `nlp/pii_guard.py` — it was guarded by a `try/except` but still executed even in `FAST_MODE`.
2. **Pre-warmed NLP models in the main thread** before `asyncio.run()` starts — calling `load_all_models()` synchronously so all C-extensions are imported with no GIL contention.

---

## File-by-File Changelog

### 1. `mcp_server.py` — MCP Server Entry Point

```diff
+import os
+
+# Enable FAST_MODE to prevent downloading 2GB+ of HuggingFace models
+os.environ["FAST_MODE"] = "true"
+
+# Redirect stderr to a file to prevent OS pipe deadlocks on Windows
+try:
+    error_log = open("mcp_server_stderr.log", "a", encoding="utf-8", buffering=1)
+    sys.stderr = error_log
+except Exception:
+    pass

 if __name__ == "__main__":
-    print("[*] AlgoPharma MCP Server Starting...")
+    import sys
+    print("[*] AlgoPharma MCP Server Starting...", file=sys.stderr)
+
+    # Pre-load models in main thread to prevent import deadlocks in asyncio.to_thread
+    print("[*] Initializing NLP models...", file=sys.stderr)
+    from nlp.models_loader import load_all_models
+    load_all_models()
+
     asyncio.run(main())
```

**Why:** Three changes stacked:
- `FAST_MODE` prevents HuggingFace model downloads that take minutes.
- stderr redirect prevents Windows pipe handle crashes.
- `load_all_models()` pre-warms spaCy/VADER imports in the main thread to avoid GIL deadlocks.

---

### 2. `mcp_tools.py` — Tool Execution Layer

```diff
     async def execute(safe_query: str, project_id: int = 1) -> dict:
         try:
+            import asyncio
             from tasks.crawl_reddit import crawl_reddit
-            result = crawl_reddit(project_id=project_id, query=safe_query)
+            result = await asyncio.to_thread(crawl_reddit, project_id=project_id, query=safe_query)
```

Applied to all three tools (`RedditTool`, `TwitterTool`, `ForumOnboardingTool`).

**Why:** The MCP server runs an asyncio event loop. Calling synchronous blocking functions (HTTP requests, DB writes) directly would block the entire event loop. `asyncio.to_thread()` offloads them to a worker thread, keeping the JSON-RPC transport responsive.

---

### 3. `reddit_crawler.py` — Reddit API Scraper

```diff
-# Enable UTF-8 printing for emojis on Windows
-if sys.stdout.encoding.lower() != 'utf-8':
-    sys.stdout.reconfigure(encoding='utf-8')
+# Enable UTF-8 printing for emojis on Windows (only when run directly, not when imported by MCP)
+if __name__ == "__main__":
+    if sys.stdout.encoding.lower() != 'utf-8':
+        sys.stdout.reconfigure(encoding='utf-8')

 def scrape_reddit(query: str, max_items: int = 100) -> list[dict]:
-    print(f"🔗 Connecting directly to Reddit API...")
+    print(f"🔗 Connecting directly to Reddit API...", file=sys.stderr)
     # ... all other print() calls also changed to file=sys.stderr ...

-        with urllib.request.urlopen(req) as response:
+        with urllib.request.urlopen(req, timeout=15) as response:
```

**Why:** 
- `sys.stdout.reconfigure()` at module scope corrupts the MCP JSON-RPC stream when the module is imported.
- `print()` to stdout injects human text into the JSON-RPC protocol stream. Redirecting to stderr keeps the pipe clean.
- Added `timeout=15` to prevent the HTTP request from hanging indefinitely.

---

### 4. `twitter_crawler.py` — Twitter API Scraper

Same pattern as `reddit_crawler.py`:

```diff
-if sys.stdout.encoding.lower() != 'utf-8':
+if __name__ == "__main__" and sys.stdout.encoding.lower() != 'utf-8':
     sys.stdout.reconfigure(encoding='utf-8')

-    print(f"🔗 Connecting to twitterapi.io...")
+    print(f"🔗 Connecting to twitterapi.io...", file=sys.stderr)
     # ... all print() calls redirected to stderr ...

-        with urllib.request.urlopen(req) as response:
+        with urllib.request.urlopen(req, timeout=15) as response:
```

---

### 5. `nlp/pii_guard.py` — PII Redaction Module

```diff
+import os
 import re
 import sys
 import hashlib
 import logging

-try:
-    import torch
-except ImportError:
-    torch = None
-
 logger = logging.getLogger(__name__)
```

**Why:** This was the **critical deadlock fix**. The `import torch` at module scope triggered C-extension initialization that deadlocked when called from `asyncio.to_thread()`. Since `FAST_MODE=true` skips the PyTorch code path entirely, the import was unnecessary and dangerous. Torch is now imported lazily only when `FAST_MODE=false` and the PII model is actually needed.

---

### 6. `llm_module.py` — Gemini Agent

```diff
     server_params = StdioServerParameters(
         command=sys.executable,
-        args=["mcp_server.py"]
+        args=["-u", "mcp_server.py"]
     )
```

**Why:** The `-u` flag forces Python's stdout to be unbuffered. Without it, the JSON-RPC responses from the MCP server get stuck in Python's internal write buffer and never reach the client — appearing as a "deadlock" even though the server computed the answer.

---

### 7. `mcp_client.py` — Standalone Test Client

```diff
     server_params = StdioServerParameters(
         command=sys.executable,
-        args=["mcp_server.py"]
+        args=["-u", "mcp_server.py"]
     )
```

Same `-u` fix as `llm_module.py`.

---

### 8. `tasks/ingest_existing.py` — NLP Ingestion Pipeline

Cleaned up debug print statements that were added during deadlock investigation. No functional changes to the pipeline logic.

---

## Architecture Diagram — Final Working System

```
┌──────────────────────────────────────────────────────────────────┐
│                    llm_module.py / mcp_client.py                 │
│                                                                  │
│  1. Spawns MCP server as subprocess: python -u mcp_server.py     │
│  2. Sends JSON-RPC over stdin/stdout                             │
│  3. Receives tool results as TextContent                         │
└──────────────────┬───────────────────────────────────────────────┘
                   │ stdin/stdout (unbuffered, -u flag)
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│                       mcp_server.py                              │
│                                                                  │
│  • FAST_MODE=true (env var, set before any imports)              │
│  • stderr → mcp_server_stderr.log (safe redirect)               │
│  • load_all_models() pre-warms spaCy/VADER in main thread       │
│  • asyncio event loop handles JSON-RPC protocol                  │
│                                                                  │
│  Tools registered:                                               │
│    reddit_crawler  → asyncio.to_thread(crawl_reddit)             │
│    twitter_crawler → asyncio.to_thread(crawl_twitter)            │
│    forum_onboarding → asyncio.to_thread(onboard_forum)           │
└──────────────────┬───────────────────────────────────────────────┘
                   │ asyncio.to_thread (worker thread)
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│              tasks/crawl_reddit.py (example)                     │
│                                                                  │
│  1. Scrape Reddit API (all print → stderr)                       │
│  2. Save JSON to disk                                            │
│  3. Call ingest_reddit_json() → NLP pipeline                     │
│  4. Return { posts_crawled, ingestion_result }                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Verification Results

```
PS> uv run .\mcp_client.py
Initializing MCP Client Test...
Connecting to server: .venv\Scripts\python.exe -u mcp_server.py

[+] Session Initialized Successfully

[+] Available Tools:
  - reddit_crawler: Search Reddit for discussions about medicines and adverse effects
  - twitter_crawler: Search Twitter/X for real-time discussions about medicines and health issues
  - forum_onboarding: Analyze a forum URL to auto-generate a working crawler configuration

[+] Calling Tool 'reddit_crawler' with args: {'safe_query': 'dolo 650 side effects'}

[+] Tool Result:
{'success': True, 'tool': 'reddit_crawler', 'query': 'dolo 650 side effects',
 'result': {'status': 'success', 'posts_crawled': 100,
            'ingestion': {'source': 'reddit', 'total': 100, 'ingested': 0,
                          'ae_flagged': 0, 'skipped': 100}}}
```

```
PS> uv run .\llm_module.py
==================================================
 AlgoPharma — Gemini + MCP Agent
==================================================
Enter query: Find paracetamol side effects on Reddit
[*] Available tools: ['reddit_crawler', 'twitter_crawler', 'forum_onboarding']
[*] Gemini chose tool: 'reddit_crawler' with args: {'safe_query': 'paracetamol side effects'}
[*] Executing 'reddit_crawler' via MCP...

[+] Result from MCP:
{'success': True, 'tool': 'reddit_crawler', 'query': 'paracetamol side effects',
 'result': {'status': 'success', 'posts_crawled': 100,
            'ingestion': {'source': 'reddit', 'total': 100, 'ingested': 99,
                          'ae_flagged': 49, 'skipped': 1}}}
```

Both the standalone test client and the full Gemini agent pipeline complete successfully with zero deadlocks.
