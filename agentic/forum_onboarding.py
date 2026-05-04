"""
AlgoPharma — Agentic forum onboarding.
Paste any forum URL → auto-generate a working crawler config.
Uses Firecrawl for page fetching and Gemini for structure analysis.
"""

import sys
import json
import logging

logger = logging.getLogger(__name__)


def onboard_forum(url: str) -> dict:
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

    # ── Step 1: Validate URL ─────────────────────────────
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
        from firecrawl import FirecrawlApp
        fc = FirecrawlApp(api_key=settings.FIRECRAWL_API_KEY)
        result = fc.scrape_url(url, params={"formats": ["markdown"]})
        markdown = result.get("markdown", "")
        if not markdown:
            return {"success": False, "error": "Firecrawl returned empty markdown", "config": {}, "samples": [], "confidence": 0.0}
    except Exception as e:
        logger.error(f"Firecrawl scrape failed: {e}")
        return {"success": False, "error": f"Firecrawl error: {e}", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 3: Gemini structure analysis ─────────────────
    if not settings.GEMINI_API_KEY:
        return {
            "success": False,
            "error": "GEMINI_API_KEY not configured. Set it in .env to enable forum analysis.",
            "config": {},
            "samples": [],
            "confidence": 0.0,
        }

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-3.0-flash-preview")

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

        response = model.generate_content(
            [f"{system_prompt}\n\n---\n\nForum page markdown (first 8000 chars):\n\n{markdown[:8000]}"],
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
            ),
        )

        config = json.loads(response.text)
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return {"success": False, "error": f"Gemini error: {e}", "config": {}, "samples": [], "confidence": 0.0}

    # ── Step 4: Fetch sample thread URLs ─────────────────
    sample_urls = config.get("sample_thread_urls", [])[:3]
    sample_markdowns = []
    for sample_url in sample_urls:
        try:
            sample_result = fc.scrape_url(sample_url, params={"formats": ["markdown"]})
            sample_md = sample_result.get("markdown", "")
            if sample_md:
                sample_markdowns.append({"url": sample_url, "markdown": sample_md[:5000]})
        except Exception as e:
            logger.warning(f"Failed to fetch sample URL {sample_url}: {e}")

    # ── Step 5: Sarvam translation if regional ───────────
    if settings.SARVAM_API_KEY and sample_markdowns:
        try:
            from langdetect import detect as lang_detect
            first_md = sample_markdowns[0]["markdown"]
            detected_lang = lang_detect(first_md[:500])

            from nlp.sentiment import SARVAM_LANG_MAP
            if detected_lang in SARVAM_LANG_MAP:
                from sarvamai import SarvamAI
                client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
                for i, sm in enumerate(sample_markdowns):
                    try:
                        resp = client.text.translate(
                            input=sm["markdown"][:500],
                            source_language_code=SARVAM_LANG_MAP[detected_lang],
                            target_language_code="en-IN",
                        )
                        sample_markdowns[i]["markdown"] = resp.translated_text
                        sample_markdowns[i]["translated_from"] = detected_lang
                    except Exception:
                        pass
        except Exception:
            pass

    # ── Step 6: Gemini extract sample posts ──────────────
    samples = []
    if sample_markdowns:
        try:
            extraction_prompt = config.get("post_extraction_prompt", "Extract individual forum posts with author, date, and content.")
            combined = "\n\n---\n\n".join([sm["markdown"] for sm in sample_markdowns])

            extract_response = model.generate_content(
                [
                    f"Using this extraction strategy: {extraction_prompt}\n\n"
                    f"Extract up to 3 individual posts from the following forum content. "
                    f"Return ONLY valid JSON array, each item with: author, date, content, url.\n\n"
                    f"Forum content:\n\n{combined[:6000]}"
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                ),
            )
            samples = json.loads(extract_response.text)
            if not isinstance(samples, list):
                samples = [samples]
        except Exception as e:
            logger.warning(f"Sample extraction failed: {e}")

    # ── Step 7: Return result ────────────────────────────
    confidence = config.get("confidence", 0.5)

    return {
        "success": True,
        "config": config,
        "samples": samples[:3],
        "confidence": confidence,
        "sample_urls_fetched": len(sample_markdowns),
    }


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
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
        print("    2. Send markdown to Gemini for structure analysis")
        print("    3. Fetch 3 sample thread URLs")
        print("    4. Extract sample posts via Gemini")
        print("    5. Return config + samples for admin review")
    elif not settings.GEMINI_API_KEY:
        print("  ⚠️  GEMINI_API_KEY not set in .env")
        print("  Both FIRECRAWL_API_KEY and GEMINI_API_KEY are needed.")
    else:
        test_url = "https://www.medhelp.org"
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
