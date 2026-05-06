# Proposal: Decoupled MCP Architecture for AlgoPharma

> **TL;DR** — Move the heavy NLP pipeline (PII redaction, NER, sentiment, AE detection) out of the MCP tool execution path. MCP tools should only crawl and return raw data; the NLP processing runs separately afterward, either in the calling script or via a Celery worker queue.

---

## 1. Problem Statement

The current architecture tightly couples **data crawling** and **NLP processing** inside every MCP tool call:

```
Gemini Agent ──► MCP Server ──► Crawl Reddit ──► NLP Pipeline (PII + NER + Sentiment + AE) ──► DB Write ──► Return
                                                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                                 This block causes deadlocks, timeouts,
                                                 and multi-minute hangs
```

### What Goes Wrong

| Issue | Root Cause | Impact |
|---|---|---|
| **OS-level import deadlock** | PyTorch / spaCy C-extensions spawn OpenMP thread-pools during import. When imported inside `asyncio.to_thread`, the GIL import lock clashes with the main asyncio event loop. | MCP server hangs permanently — requires `kill -9`. |
| **Multi-minute tool latency** | Processing 100 posts through 5 NLP stages (PII, lang-detect, NER, sentiment, AE) takes 30–60 seconds synchronously. | Gemini's RPC times out; user stares at a frozen terminal. |
| **Blast radius** | A single malformed Reddit post crashing `langdetect` or `pii_guard` kills the *entire* MCP tool call, even though 99 posts were already successfully crawled. | Crawled data is lost; must re-fetch from Reddit API. |
| **Resource coupling** | MCP server process must hold enough RAM for both HTTP I/O *and* transformer model weights (~2 GB). | Cannot run on a small VM; no independent scaling. |

We have **already worked around** the deadlock (see the MCP Implementation Log below), but the workarounds are fragile:

- `FAST_MODE=true` disables the best NLP models, reducing detection quality.
- Pre-warming models in the main thread adds 4–8s to MCP server startup.
- The architecture is still synchronous — the agent *waits* for NLP to finish.

---

## 2. Proposed Architecture

Split the pipeline into two independent phases:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        PHASE 1 — AGENTIC (fast)                        │
│                                                                         │
│   User ──► Gemini Agent ──► MCP Server ──► Crawl Reddit/Twitter         │
│                                   │                                     │
│                                   ├── Save raw JSON to disk             │
│                                   ├── Log CrawlLog entry (status=done)  │
│                                   └── Return { posts_crawled: 100 }     │
│                                                                         │
│   Latency: ~2 seconds                                                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     PHASE 2 — PROCESSING (async)                       │
│                                                                         │
│   Option A: Inline in llm_module.py (simple, no infra)                  │
│   Option B: Celery worker task   (scalable, production)                │
│   Option C: Agent tool `ingest_data` (agentic, LLM-driven)            │
│                                                                         │
│   Runs: PII → NER → Sentiment → AE Detection → DB Write               │
│                                                                         │
│   Can use full-weight models (no FAST_MODE needed)                      │
│   Failures are retryable without re-crawling                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Design Options for Phase 2

### Option A: Inline Processing in `llm_module.py` (Recommended for Hackathon)

The simplest approach. After the MCP tool returns the crawled data, the calling script (`llm_module.py`) triggers ingestion directly:

```python
# In llm_module.py, after MCP tool returns:
result = await session.call_tool("reddit_crawler", tool_args)

# Phase 2: Run NLP pipeline locally (outside MCP)
from tasks.ingest_existing import ingest_reddit_json
ingestion = ingest_reddit_json(project_id=1)
print(f"Processed {ingestion['ingested']} posts, {ingestion['ae_flagged']} adverse events flagged")
```

**Pros:** Zero infrastructure changes. Works immediately.
**Cons:** Still synchronous from the user's perspective. Blocks the terminal during NLP processing.

---

### Option B: Celery Worker Queue (Recommended for Production)

We already have `celery_app.py` with registered tasks. The MCP tool fires a Celery task and returns immediately:

```python
# In mcp_tools.py RedditTool.execute():
from celery_app import task_ingest_all
task_ingest_all.delay(project_id)  # Fire-and-forget
return {"success": True, "posts_crawled": len(posts), "processing": "queued"}
```

**Pros:** True async. Scales horizontally. Full-weight models on GPU workers.
**Cons:** Requires Redis. More infra to manage.

---

### Option C: Expose `ingest_data` as a Separate MCP Tool (Agentic)

Add a new MCP tool that the agent can call *after* crawling:

```python
class IngestTool:
    name = "ingest_data"
    description = "Process previously crawled data through the NLP pipeline"
    # ...
```

The Gemini agent would then autonomously decide:
1. First call `reddit_crawler` → gets back `{ posts_crawled: 100 }`
2. Then call `ingest_data` → gets back `{ ae_flagged: 49 }`

**Pros:** Fully agentic. Agent decides when/whether to process.
**Cons:** Requires multi-turn tool calling. Still runs NLP inside MCP process.

---

## 4. Comparison Matrix

| Criteria | Current (Coupled) | Option A (Inline) | Option B (Celery) | Option C (Agentic) |
|---|---|---|---|---|
| MCP server stability | ❌ Fragile | ✅ Rock-solid | ✅ Rock-solid | ⚠️ Medium |
| Agent response time | ❌ 30–60s | ⚠️ 2s + 30s | ✅ 2s | ⚠️ 2s + 30s |
| Full NLP models | ❌ FAST_MODE only | ✅ Full | ✅ Full | ⚠️ Needs pre-warm |
| Fault isolation | ❌ All-or-nothing | ✅ Crawl safe | ✅ Crawl safe | ✅ Crawl safe |
| Infra complexity | ✅ None | ✅ None | ⚠️ Redis needed | ✅ None |
| Hackathon-ready | ✅ Works now | ✅ 30 min change | ⚠️ Hours | ⚠️ Hours |

---

## 5. Recommendation

### For the Hackathon Demo: **Option A**

- Change MCP tools to *only crawl and save JSON*.
- After the MCP call returns in `llm_module.py`, call `ingest_reddit_json()` / `ingest_twitter_json()` directly.
- This gives us full-weight NLP models, fault isolation, and a ~2s agent response — all with minimal code changes.

### For Production: **Option B**

- The Celery infrastructure is already scaffolded in `celery_app.py`.
- Tasks `algopharma.crawl_reddit`, `algopharma.ingest_all` are already registered.
- Just requires spinning up a Redis instance and a Celery worker process.

---

## 6. Implementation Plan (Option A)

### Step 1: Slim down MCP tools (crawl-only)

Modify `tasks/crawl_reddit.py` and `tasks/crawl_twitter.py` to:
- Crawl data from the API
- Save raw JSON to disk
- Log `CrawlLog` entry
- **Remove** the call to `ingest_reddit_json()` / `ingest_twitter_json()`
- Return `{ status, posts_crawled, json_path }`

### Step 2: Move ingestion to `llm_module.py`

After the MCP tool call returns, run the NLP pipeline in the calling process:

```python
result = await session.call_tool(tool_name, tool_args)
# ... print crawl result ...

# Phase 2: Process the crawled data
if tool_name == "reddit_crawler":
    from tasks.ingest_existing import ingest_reddit_json
    ingestion = ingest_reddit_json(project_id=1)
elif tool_name == "twitter_crawler":
    from tasks.ingest_existing import ingest_twitter_json
    ingestion = ingest_twitter_json(project_id=1)
```

### Step 3: Remove FAST_MODE and model pre-warming from MCP server

Since the MCP server no longer runs NLP, we can remove:
- `os.environ["FAST_MODE"] = "true"` from `mcp_server.py`
- The `load_all_models()` pre-warm call
- The `import torch` removal hack in `pii_guard.py`

### Step 4: Enable full NLP models in `llm_module.py`

The calling script can now safely load full-weight models because it runs in its own process with no stdio pipe constraints.

---

## 7. Migration Risk Assessment

| Risk | Mitigation |
|---|---|
| `ingest_reddit_json` fails in `llm_module.py` context | Same Python environment; already tested standalone. Low risk. |
| Agent loses immediate AE count | Agent can print "Processing..." then print results after ingestion. |
| Breaking existing `test_pipeline.py` | `test_pipeline.py` calls crawl tasks directly; unaffected. |
| Forum onboarding tool | Forum onboarding doesn't use NLP pipeline — no change needed. |

---

## 8. Success Criteria

- [ ] MCP tool call (`reddit_crawler`) returns in **< 5 seconds**
- [ ] NLP pipeline runs successfully **outside** the MCP server process
- [ ] No `FAST_MODE` needed — full PII/NER/sentiment models active
- [ ] Zero deadlocks after 10 consecutive test runs
- [ ] Agent provides crawl confirmation + processing results to user
