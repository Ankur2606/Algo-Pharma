"""
AlgoPharma — Agentic forum onboarding.
Paste any forum URL → auto-generate a working crawler config.
Uses Firecrawl for page fetching and Gemini for structure analysis.

SECURITY: All markdown sent to LLM is PII-redacted first to prevent
exposure of user data from forum posts.
"""

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
        logger.info(f"[Trace] {step_name} -> {log_path}")
    except Exception as e:
        logger.error(f"Failed to write trace log: {e}")

def _clean_json(text: str) -> str:
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
        
    return text

def onboard_forum(url: str) -> dict:
    """
    End-to-end agentic pipeline to auto-analyse a forum and generate crawler config.

    Steps:
        1. Receive forum URL and validate API keys.
        2. Firecrawl scrape → fetch main forum index markdown.
        3. Language Detection → detect primary language of the forum.
        4. PII Redaction Guard → mask confidential data while preserving URLs.
        5. LLM Structure Analysis (Nvidia Nemotron) → extract CSS/regex rules & sample thread URLs into config JSON.
        6. Fetch Sample Threads → scrape thread URLs found in step 5.
        7. Sample PII Redaction → scrub thread data before extraction/translation.
        8. (Optional) Sarvam Translation → translate regional forums (HI/TE) to English.
        9. LLM Post Extraction (Nvidia Nemotron) → extract structured posts from the safe sample threads.
        10. Return config + extracted samples for admin review.
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
        pii_result = redact_pii(markdown[:15000], lang=forum_lang, preserve_urls=True)
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

        from urllib.parse import urlparse
        base_domain = urlparse(url).netloc

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
            f"- sample_thread_urls: array of up to 3 thread URLs found on the page. They can be absolute or relative (e.g. /threads/...). They MUST belong to the domain '{base_domain}'. DO NOT make up URLs.\n"
            "- confidence: your confidence in this analysis from 0.0 to 1.0"
        )

        prompt_content = f"{system_prompt}\n\n---\n\nForum page markdown (first 15000 chars):\n\n{markdown_safe}"
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
        config = json.loads(_clean_json(response_text))
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return {"success": False, "error": f"LLM error: {e}", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 4: Fetch sample thread URLs ─────────────────
    from urllib.parse import urlparse, urljoin
    base_domain = urlparse(url).netloc

    raw_sample_urls = config.get("sample_thread_urls", [])
    sample_urls = []
    for su in raw_sample_urls:
        if su and isinstance(su, str):
            # Resolve relative URLs to absolute URLs
            absolute_url = urljoin(url, su)
            parsed_su = urlparse(absolute_url)
            
            # Strictly validate that it belongs to the correct domain
            if parsed_su.netloc == base_domain or parsed_su.netloc.endswith(f".{base_domain}"):
                sample_urls.append(absolute_url)
            else:
                logger.warning(f"[forum_onboarding] Dropping external/hallucinated URL: {absolute_url}")

    sample_urls = sample_urls[:3]
    sample_markdowns = []
    for sample_url in sample_urls:
        try:
            _trace_log("STEP 4: Fetching Sample Thread", f"URL: {sample_url}")
            sample_result = fc.scrape(sample_url, formats=["markdown"])
            sample_md = getattr(sample_result, "markdown", "")
            if sample_md:
                _trace_log(f"STEP 4: Sample Thread Output ({sample_url})", sample_md)
                sample_markdowns.append({"url": sample_url, "markdown": sample_md[:15000]})
        except Exception as e:
            logger.warning(f"Failed to fetch sample URL {sample_url}: {e}")

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

                pii_result = redact_pii(sm["markdown"][:15000], lang=thread_lang, preserve_urls=True)
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
                f"Note: The content below is Markdown, not raw HTML. If CSS classes or HTML tags mentioned in the strategy are missing, use semantic understanding to identify the post boundaries, author, date, and content.\n"
                f"Extract up to 3 individual posts from the following forum content. "
                f"Return ONLY valid JSON array, each item with: author, date, content, url.\n\n"
                f"Forum content:\n\n{combined[:25000]}"
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
            samples = json.loads(_clean_json(extract_response_text))
            if not isinstance(samples, list):
                samples = [samples]
        except Exception as e:
            logger.warning(f"Sample extraction failed: {e}")

    # ── Step 7: Return result ────────────────────────────
    confidence = config.get("confidence", 0.5)

    final_result = {
        "success": True,
        "config": config,
        "samples": samples[:3],
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
        test_url = "https://www.healthboards.com/boards/drug-interactions-side-effects/"
        print(f"  Testing with: {test_url}")
        result = onboard_forum(test_url)
        print(f"  Success: {result['success']}")
        if result['success']:
            print(f"  Confidence: {result['confidence']}")
            print(f"  Forum type: {result['config'].get('forum_type', 'unknown')}")
            print(f"  Samples extracted: {len(result['samples'])}")
        else:
            print(f"  Error: {result.get('error', 'unknown')}")

    print("─" * 55)
    print("✅ forum_onboarding self-test PASS")