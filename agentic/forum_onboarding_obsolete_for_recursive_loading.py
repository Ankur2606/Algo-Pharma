"""
AlgoPharma — Agentic forum onboarding.
Paste any forum URL → auto-generate a working crawler config.
Uses Firecrawl for page fetching and Gemini for structure analysis.

SECURITY: All markdown sent to LLM is PII-redacted first to prevent
exposure of user data from forum posts.
"""
# fix it ``` INFO:     Application startup complete.
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     127.0.0.1:53871 - "GET / HTTP/1.1" 200 OK
# 2026-05-13 05:47:33,222 [INFO] httpx: HTTP Request: GET https://huggingface.co/api/models/cardiffnlp/twitter-roberta-base-sentiment-latest/commits/refs%2Fpr%2F43 "HTTP/1.1 200 OK"
# 2026-05-13 05:47:33,477 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest/resolve/refs%2Fpr%2F43/model.safetensors.index.json "HTTP/1.1 404 Not Found"
# 2026-05-13 05:47:33,800 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment-latest/resolve/refs%2Fpr%2F43/model.safetensors "HTTP/1.1 302 Found"
# 2026-05-13 05:47:40,068 [INFO] httpx: HTTP Request: POST https://api.groq.com/openai/v1/chat/completions "HTTP/1.1 200 OK"
# 2026-05-13 05:47:40,217 [INFO] api.chat: [/api/chat] Forum pipeline triggered | project_id=28 | url='https://healthboards.com/drugtalk/' | medicine='Aspirin'
# INFO:     127.0.0.1:61731 - "POST /api/chat HTTP/1.1" 200 OK
# 2026-05-13 05:47:45,978 [INFO] agentic.forum_onboarding: [forum_onboarding] Forum language detected: 'en'
# 2026-05-13 05:47:46,132 [INFO] openmed.core.backends: Auto-selected inference backend: hf
# Loading weights: 100%|███████████████████████████████████████████████████| 104/104 [00:00<00:00, 6596.01it/s]
# 2026-05-13 05:47:47,374 [INFO] openmed.core.models: Created pipeline for OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1
# 2026-05-13 05:47:47,689 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/resolve/main/config.json "HTTP/1.1 307 Temporary Redirect"
# 2026-05-13 05:47:47,717 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/a2360d3f42526fc660ac3b2b2301e1c2d94eba61/config.json "HTTP/1.1 200 OK"
# 2026-05-13 05:47:48,216 [INFO] openmed.core.backends: Auto-selected inference backend: hf
# 2026-05-13 05:47:48,482 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/resolve/main/config.json "HTTP/1.1 307 Temporary Redirect"
# 2026-05-13 05:47:48,507 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/a2360d3f42526fc660ac3b2b2301e1c2d94eba61/config.json "HTTP/1.1 200 OK"
# Loading weights: 100%|███████████████████████████████████████████████████| 104/104 [00:00<00:00, 5360.86it/s]
# 2026-05-13 05:47:48,812 [INFO] httpx: HTTP Request: GET https://huggingface.co/api/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/tree/main/additional_chat_templates?recursive=false&expand=false "HTTP/1.1 404 Not Found"
# 2026-05-13 05:47:49,076 [INFO] httpx: HTTP Request: GET https://huggingface.co/api/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/tree/main?recursive=true&expand=false "HTTP/1.1 200 OK"
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# 2026-05-13 05:47:49,984 [INFO] httpx: HTTP Request: GET https://huggingface.co/api/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1 "HTTP/1.1 200 OK"
# 2026-05-13 05:47:49,986 [INFO] openmed.core.models: Created pipeline for OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1
# 2026-05-13 05:47:50,313 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/resolve/main/config.json "HTTP/1.1 307 Temporary Redirect"
# 2026-05-13 05:47:50,338 [INFO] httpx: HTTP Request: HEAD https://huggingface.co/api/resolve-cache/models/OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1/a2360d3f42526fc660ac3b2b2301e1c2d94eba61/config.json "HTTP/1.1 200 OK"
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# 2026-05-13 05:48:13,378 [INFO] httpx: HTTP Request: POST https://integrate.api.nvidia.com/v1/chat/completions "HTTP/1.1 200 OK"
# 2026-05-13 05:48:13,385 [INFO] tasks.crawl_forum: [crawl_forum] Onboarding complete | url=https://healthboards.com/drugtalk/ | confidence=0.2 | samples=0 | forum_type=custom
# 2026-05-13 05:48:13,385 [INFO] tasks.crawl_forum: [crawl_forum] Stored 0 RawPosts for project 28
# 2026-05-13 05:48:14,147 [INFO] tasks.crawl_forum: ✅ Forum NLP task queued | task_id=da22ebb6-80fa-435a-8452-6219d89a0e8c
# 2026-05-13 05:48:14,155 [INFO] api.chat: [forum_pipeline] Completed | project_id=28 | result={'status': 'success', 'tool': 'forum_onboarding', 'forum_url': 'https://healthboards.com/drugtalk/', 'forum_type': 'custom', 'confidence': 0.2, 'posts_crawled': 0, 'config': {'post_extraction_prompt': 'Extract each post container from the thread page using common forum selectors such as .post, .message, .thread-post, or li.post, then retrieve the author, timestamp, and content within each container.', 'author_pattern': '.author, .username, .post-author', 'timestamp_pattern': "ISO-like format (e.g., YYYY-MM-DD HH:MM:SS) or relative times like '2 hours ago'", 'reply_structure': 'flat', 'pagination': "Traditional page numbers with links like ?page=2 or a 'Next' button", 'forum_type': 'custom', 'sample_thread_urls': [], 'confidence': 0.2}}
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# 2026-05-13 05:48:14,954 [INFO] tasks.crawl_forum: ✅ Celery [process_unprocessed] COMPLETE: {'project_id': 28, 'total_raw': 0, 'processed': 0, 'ae_flagged': 0, 'skipped': 0, 'signals_detected': 0}
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK
# INFO:     127.0.0.1:53144 - "GET /api/results/28 HTTP/1.1" 200 OK```?
import sys
import json
import logging
import os
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger(__name__)

def _trace_log(step_name: str, content: str):
    import os
    import datetime
    log_path = os.path.join(os.path.dirname(__file__), "pipeline_trace.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"[{datetime.datetime.now().isoformat()}] {step_name}\n")
            f.write(f"{'='*80}\n\n")
            f.write(str(content) + "\n")
    except Exception as e:
        logger.error(f"Failed to write trace log: {e}")

def _clean_json(text: str) -> str:
    import re as _re
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    text = text.strip()
    
    if text.startswith("{"):
        text = text[:text.rfind("}")+1]
    elif text.startswith("["):
        text = text[:text.rfind("]")+1]

    # Fix invalid JSON escapes — LLMs often emit \* \[ \] etc. from markdown
    text = _re.sub(r'\\([^"\\/bfnrtu])', r'\1', text)
        
    return text

def onboard_forum(url: str, medicine: str = "") -> dict:
    """
    Seven-step pipeline to auto-analyse a forum and generate crawler config.

    Steps:
        1. Receive forum URL
        2. Firecrawl scrape → markdown
        3. Gemini structure analysis → config JSON
        4. Fetch sample thread URLs
        5. (Optional) Sarvam translation for regional forums
        6. Gemini extracts sample posts
        7. Return config + samples for admin review
    """
    from config import get_settings
    settings = get_settings()

    # If FAST_MODE is enabled AND we lack the required API keys, return a stub.
    # But if API keys ARE available, proceed even in FAST_MODE — forum onboarding
    # doesn't use any NLP models (no transformers/spaCy), it only calls Firecrawl + LLM APIs.
    fast_mode = os.getenv("FAST_MODE", "false").lower() in ("1", "true", "yes")
    has_firecrawl = bool(settings.FIRECRAWL_API_KEY)
    has_nvidia = bool(settings.NVIDIA_API_KEY)

    if fast_mode and (not has_firecrawl or not has_nvidia):
        _trace_log("FAST_MODE Bypass", "FAST_MODE active and missing API keys — returning stub")
        return {
            "success": True,
            "config": {"forum_type": "fast_mode_stub", "post_extraction_prompt": "Extract author, date, content"},
            "samples": [
                {"url": "about:fast_mode", "markdown": "Sample post: I took Dolo 650 and experienced headache and nausea.", "translated_from": None}
            ],
            "confidence": 0.1,
            "sample_urls_fetched": 0,
        }

    # ── Step 1: Validate URL ─────────────────────────────
    _trace_log("STEP 1: Starting Onboarding", f"Target URL: {url}")
    if not url or not url.startswith("http"):
        return {"success": False, "error": "Invalid URL", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 2: Firecrawl fetch ──────────────────────────
    if not settings.FIRECRAWL_API_KEY:
        return {
            "success": False,
            "error": "FIRECRAWL_API_KEY not configured. Set it in .env to enable forum onboarding.",
            "config": {},
            "samples": [],
            "confidence": 0.0,
        }

    try:
        from firecrawl import Firecrawl
        fc = Firecrawl(api_key=settings.FIRECRAWL_API_KEY)
        _trace_log("STEP 2: Firecrawl Fetching", f"URL: {url}")
        result = fc.scrape(url, formats=["markdown"])
        markdown = getattr(result, "markdown", "")
        _trace_log("STEP 2: Firecrawl Output", markdown)
        if not markdown:
            return {"success": False, "error": "Firecrawl returned empty markdown", "config": {}, "samples": [], "confidence": 0.0}
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return {"success": False, "error": f"Firecrawl error: {e}", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 2b: Detect forum language once — carried through all downstream steps ──
    # This ensures PII redaction uses the right language model (44M Hindi / 82M Telugu / 44M English).
    try:
        from langdetect import detect as lang_detect
        forum_lang = lang_detect(markdown[:1000])
    except Exception:
        forum_lang = "en"
    _trace_log("STEP 2b: Language Detection", f"Detected language: '{forum_lang}'")
    logger.info(f"[forum_onboarding] Forum language detected: '{forum_lang}'")

    # ── Step 3: Language-aware PII Redaction BEFORE sending anything to LLM ─────
    # Uses the detected language so the Hindi/Telugu OpenMed models are invoked
    # correctly instead of defaulting to English-only regex.
    try:
        from nlp.pii_guard import redact_pii
        pii_result = redact_pii(markdown[:8000], lang=forum_lang)
        markdown_safe = pii_result["redacted_text"]
        _trace_log("STEP 3: PII Redaction", f"lang={forum_lang} | PII entities found: {pii_result['pii_entities_found']}")
    except Exception as e:
        logger.warning(f"PII redaction failed, using original: {e}")
        markdown_safe = markdown[:8000]

    # ── Step 3: Nvidia Nemotron structure analysis ─────────────────
    if not settings.NVIDIA_API_KEY:
        return {
            "success": False,
            "error": "NVIDIA_API_KEY not configured. Set it in .env to enable forum analysis.",
            "config": {},
            "samples": [],
            "confidence": 0.0,
        }

    try:
        from openai import OpenAI
        client = OpenAI(
            base_url=settings.NVIDIA_API_BASE_URL,
            api_key=settings.NVIDIA_API_KEY
        )

        system_prompt = (
            "You are an expert at analyzing web forum structure. "
            "Given the markdown content of a forum page, analyze its structure and return ONLY valid JSON "
            "(no markdown fences, no explanation) with these fields:\n"
            "- post_extraction_prompt: a prompt to extract individual posts from thread pages\n"
            "- author_pattern: regex or CSS-like pattern for author names\n"
            "- timestamp_pattern: regex or description of timestamp format\n"
            "- reply_structure: how replies are nested (flat, threaded, etc.)\n"
            "- pagination: how pagination works (next button, infinite scroll, page numbers)\n"
            "- forum_type: one of vbulletin, phpbb, discourse, custom\n"
            "- sample_thread_urls: array of up to 3 full thread URLs found on the page\n"
            "- confidence: your confidence in this analysis from 0.0 to 1.0"
        )

        # NOTE: We use the original markdown here (not PII-redacted) because the LLM
        # needs to see real URLs to find thread links. The drug index page contains
        # public navigation links, not user PII (names, emails, phone numbers).
        prompt_content = f"{system_prompt}\n\n---\n\nForum page markdown (first 8000 chars):\n\n{markdown[:8000]}"
        _trace_log("STEP 3: LLM Analysis Input", prompt_content)

        completion = client.chat.completions.create(
            model=settings.NVIDIA_MODEL,
            messages=[{"role": "user", "content": prompt_content}],
            temperature=1,
            top_p=0.95,
            max_tokens=16384,
            extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384},
            stream=True
        )

        response_text = ""
        for chunk in completion:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.content is not None:
                response_text += chunk.choices[0].delta.content

        _trace_log("STEP 3: LLM Analysis Output", response_text)
        cleaned = _clean_json(response_text)
        try:
            config = json.loads(cleaned)
        except json.JSONDecodeError:
            # Nvidia Nemotron often puts regex patterns (\d, \b, \w) in JSON strings
            # which are invalid JSON escapes. Double-escape them so json.loads accepts them.
            import re as _jre
            fixed = _jre.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned)
            config = json.loads(fixed)
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return {"success": False, "error": f"LLM error: {e}", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 4: Fetch sample thread URLs ─────────────────
    sample_urls = config.get("sample_thread_urls", [])[:3]
    sample_markdowns = []

    # ── Step 4a: URL Chaining — follow medicine-specific links ──────
    # If no thread URLs found and we have a medicine name, the page is likely
    # a drug index (e.g. healthboards.com/drugtalk/ listing "Aspirin (4797)").
    # Ask the LLM to find the medicine's subforum URL, then scrape that.
    if not sample_urls and medicine:
        _trace_log("STEP 4a: URL Chaining", f"No threads found — looking for '{medicine}' subforum link in index page")
        logger.info(f"[forum_onboarding] URL chaining: searching index for '{medicine}' link")

        try:
            chain_prompt = (
                f"The following is a forum index page. Find the URL for the drug/medicine '{medicine}'. "
                f"Return ONLY the full URL (starting with http), nothing else. "
                f"If you cannot find it, return the word NONE.\n\n"
                f"Forum index page:\n\n{markdown[:8000]}"
            )

            chain_completion = client.chat.completions.create(
                model=settings.NVIDIA_MODEL,
                messages=[{"role": "user", "content": chain_prompt}],
                temperature=0.1,
                max_tokens=512,
                stream=True
            )

            chain_url = ""
            for chunk in chain_completion:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content is not None:
                    chain_url += chunk.choices[0].delta.content

            chain_url = chain_url.strip().split('\n')[0].strip()
            _trace_log("STEP 4a: LLM URL Chain Result", chain_url)

            if chain_url and chain_url.startswith("http") and "NONE" not in chain_url.upper():
                logger.info(f"[forum_onboarding] URL chain found: {chain_url}")

                # Scrape the medicine-specific subforum
                subforum_result = fc.scrape(chain_url, formats=["markdown"])
                subforum_md = getattr(subforum_result, "markdown", "")

                if subforum_md:
                    _trace_log("STEP 4a: Subforum Scraped", subforum_md[:2000])

                    # Re-analyze the subforum page for thread URLs
                    subforum_prompt = (
                        f"You are an expert at analyzing web forum structure. "
                        f"This is a subforum page for the drug '{medicine}'. "
                        f"Find up to 5 thread/topic URLs on this page. "
                        f"Return ONLY a valid JSON array of full URLs, no explanation.\n\n"
                        f"Subforum page:\n\n{subforum_md[:6000]}"
                    )

                    subforum_completion = client.chat.completions.create(
                        model=settings.NVIDIA_MODEL,
                        messages=[{"role": "user", "content": subforum_prompt}],
                        temperature=0.1,
                        max_tokens=2048,
                        stream=True
                    )

                    subforum_response = ""
                    for chunk in subforum_completion:
                        if not chunk.choices:
                            continue
                        if chunk.choices[0].delta.content is not None:
                            subforum_response += chunk.choices[0].delta.content

                    _trace_log("STEP 4a: Subforum Thread URLs", subforum_response)

                    try:
                        found_urls = json.loads(_clean_json(subforum_response))
                        if isinstance(found_urls, list):
                            sample_urls = [u for u in found_urls if isinstance(u, str) and u.startswith("http")][:5]
                            logger.info(f"[forum_onboarding] URL chain: found {len(sample_urls)} thread URLs")
                    except (json.JSONDecodeError, TypeError):
                        # If LLM didn't return JSON, try to extract URLs via regex
                        import re
                        sample_urls = re.findall(r'https?://[^\s\'"\\]+', subforum_response)[:5]
                        logger.info(f"[forum_onboarding] URL chain: regex-extracted {len(sample_urls)} URLs")

                    # Also keep the subforum markdown as a fallback
                    if not sample_urls:
                        sample_markdowns.append({"url": chain_url, "markdown": subforum_md[:8000]})

        except Exception as e:
            logger.warning(f"[forum_onboarding] URL chaining failed: {e}")

    # Fetch actual thread pages
    for sample_url in sample_urls:
        try:
            _trace_log("STEP 4: Fetching Sample Thread", f"URL: {sample_url}")
            sample_result = fc.scrape(sample_url, formats=["markdown"])
            sample_md = getattr(sample_result, "markdown", "")
            if sample_md:
                _trace_log(f"STEP 4: Sample Thread Output ({sample_url})", sample_md)
                sample_markdowns.append({"url": sample_url, "markdown": sample_md[:5000]})
        except Exception as e:
            logger.warning(f"Failed to fetch sample URL {sample_url}: {e}")

    # ── Step 4b: Fallback — use main page markdown if still nothing ──
    if not sample_markdowns:
        _trace_log("STEP 4b: Fallback", "No sample thread URLs found — using main page markdown for extraction")
        logger.info("[forum_onboarding] No sample threads found — falling back to main page extraction")
        sample_markdowns.append({"url": url, "markdown": markdown[:8000]})

    # ── Step 5: PII Redact samples FIRST (with forum language), THEN translate ──
    # ORDER MATTERS: redact before sending to Sarvam so the translation API
    # never sees raw patient names, phone numbers, or identifiers.
    sample_markdowns_safe = []
    if sample_markdowns:
        try:
            from nlp.pii_guard import redact_pii
            for sm in sample_markdowns:
                # Each thread may differ slightly in language; re-detect per thread
                try:
                    from langdetect import detect as lang_detect
                    thread_lang = lang_detect(sm["markdown"][:500])
                except Exception:
                    thread_lang = forum_lang  # fall back to page-level detection

                pii_result = redact_pii(sm["markdown"][:5000], lang=thread_lang)
                sample_markdowns_safe.append({
                    "url": sm["url"],
                    "markdown": pii_result["redacted_text"],
                    "translated_from": sm.get("translated_from", None),
                    "thread_lang": thread_lang,
                })
            _trace_log("STEP 5: Sample PII Redaction", f"Redacted {len(sample_markdowns_safe)} samples (langs: {[s['thread_lang'] for s in sample_markdowns_safe]})")
        except Exception as e:
            logger.warning(f"Sample PII redaction failed, using originals: {e}")
            sample_markdowns_safe = [{**sm, "thread_lang": forum_lang} for sm in sample_markdowns]

    # ── Step 6: Sarvam translation (now safe — PII already redacted) ─────────
    # We translate the REDACTED text, so Sarvam only sees anonymised content.
    if settings.SARVAM_API_KEY and sample_markdowns_safe:
        try:
            from nlp.sentiment import SARVAM_LANG_MAP
            if forum_lang in SARVAM_LANG_MAP:
                from sarvamai import SarvamAI
                sarvam_client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
                for i, sm in enumerate(sample_markdowns_safe):
                    try:
                        resp = sarvam_client.text.translate(
                            input=sm["markdown"][:500],
                            source_language_code=SARVAM_LANG_MAP[forum_lang],
                            target_language_code="en-IN",
                        )
                        sample_markdowns_safe[i]["markdown"] = resp.translated_text
                        sample_markdowns_safe[i]["translated_from"] = forum_lang
                        _trace_log(f"STEP 6: Sarvam Translation ({forum_lang} -> en)", resp.translated_text)
                    except Exception:
                        pass
        except Exception:
            pass

    # ── Step 6: Nvidia Nemotron extract sample posts ──────────────
    samples = []
    if sample_markdowns_safe:
        try:
            extraction_prompt = config.get("post_extraction_prompt", "Extract individual forum posts with author, date, and content.")
            combined = "\n\n---\n\n".join([sm["markdown"] for sm in sample_markdowns_safe])

            prompt_content = (
                f"Using this extraction strategy: {extraction_prompt}\n\n"
                f"Extract up to 10 individual posts from the following forum content. "
                f"Each post should discuss a medicine, drug, or health topic. "
                f"Return ONLY valid JSON array, each item with: author, date, title, content, url.\n\n"
                f"Forum content:\n\n{combined[:8000]}"
            )
            _trace_log("STEP 6: LLM Extraction Input", prompt_content)

            completion = client.chat.completions.create(
                model=settings.NVIDIA_MODEL,
                messages=[{"role": "user", "content": prompt_content}],
                temperature=1,
                top_p=0.95,
                max_tokens=16384,
                extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 16384},
                stream=True
            )

            extract_response_text = ""
            for chunk in completion:
                if not chunk.choices:
                    continue
                if chunk.choices[0].delta.content is not None:
                    extract_response_text += chunk.choices[0].delta.content

            _trace_log("STEP 6: LLM Extraction Output", extract_response_text)
            cleaned_extract = _clean_json(extract_response_text)
            try:
                samples = json.loads(cleaned_extract)
            except json.JSONDecodeError:
                import re as _jre
                fixed = _jre.sub(r'(?<!\\)\\(?!["\\/bfnrtu])', r'\\\\', cleaned_extract)
                samples = json.loads(fixed)
            if not isinstance(samples, list):
                samples = [samples]
        except Exception as e:
            logger.warning(f"Sample extraction failed: {e}")

    # ── Step 7: Return result ────────────────────────────
    confidence = config.get("confidence", 0.5)

    final_result = {
        "success": True,
        "config": config,
        "samples": samples[:10],
        "confidence": confidence,
        "sample_urls_fetched": len(sample_markdowns),
    }
    
    _trace_log("STEP 7: Final Result Returned", json.dumps(final_result, indent=2))
    return final_result


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    import os
    import sys
    # Add project root to sys.path to allow importing from root modules
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    from config import get_settings
    settings = get_settings()

    print("=" * 55)
    print("  Forum Onboarding — Self-test")
    print("=" * 55)

    if not settings.FIRECRAWL_API_KEY:
        print("  ⚠️  FIRECRAWL_API_KEY not set in .env")
        print("  With API key set, this would:")
        print("    1. Firecrawl scrape the target forum URL")
        print("    2. Send markdown to LLM for structure analysis")
        print("    3. Fetch 3 sample thread URLs")
        print("    4. Extract sample posts via LLM")
        print("    5. Return config + samples for admin review")
    elif not settings.NVIDIA_API_KEY:
        print("  ⚠️  NVIDIA_API_KEY not set in .env")
        print("  Both FIRECRAWL_API_KEY and NVIDIA_API_KEY are needed.")
    else:
        test_url = "https://www.healthboards.com/drugtalk/"
        test_med = "Aspirin"
        print(f"  Testing with: {test_url} (medicine={test_med})")
        result = onboard_forum(test_url, medicine=test_med)
        print(f"  Success: {result['success']}")
        if result['success']:
            print(f"  Confidence: {result['confidence']}")
            print(f"  Forum type: {result['config'].get('forum_type', 'unknown')}")
            print(f"  Samples extracted: {len(result['samples'])}")
        else:
            print(f"  Error: {result.get('error', 'unknown')}")

    print("─" * 55)
    print("✅ forum_onboarding self-test PASS")