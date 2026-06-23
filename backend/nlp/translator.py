"""
AlgoPharma — Regional language translation.
Uses Sarvam AI API to translate regional text to English before NER.
"""

import logging
from config import get_settings

logger = logging.getLogger(__name__)

SARVAM_LANG_MAP = {
    "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
    "ml": "ml-IN", "mr": "mr-IN", "bn": "bn-IN", "gu": "gu-IN",
    "pa": "pa-IN", "or": "or-IN", "as": "as-IN", "ur": "ur-IN",
}

REGIONAL_LANGS = set(SARVAM_LANG_MAP.keys())

def translate_to_english(text: str, lang: str) -> str:
    """
    Translate regional text to English using Sarvam AI SDK.
    If language is not regional, or translation fails, returns original text.
    """
    if lang not in REGIONAL_LANGS:
        return text

    settings = get_settings()
    if not settings.SARVAM_API_KEY:
        logger.warning("Sarvam API key not set. Skipping translation.")
        return text

    try:
        from sarvamai import SarvamAI
        client = SarvamAI(api_subscription_key=settings.SARVAM_API_KEY)
        source_lang = SARVAM_LANG_MAP.get(lang)
        
        # Sarvam Translate max char limit for robust performance is 2000
        truncated_text = text[:1900]
        
        response = client.text.translate(
            input=truncated_text,
            source_language_code=source_lang,
            target_language_code="en-IN",
        )
        translated = response.translated_text
        logger.info(f"Translated {lang} -> en via Sarvam: '{truncated_text[:30]}...' -> '{translated[:30]}...'")
        return translated
    except Exception as e:
        logger.warning(f"Sarvam translation failed for lang '{lang}': {e}. Returning original text.")
        return text

if __name__ == "__main__":
    import sys
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    
    # Test
    res = translate_to_english("मैं ऑफिस जा रहा हूँ", "hi")
    print(f"Translation Test: {res}")
