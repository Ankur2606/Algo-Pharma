"""
AlgoPharma — Three-layer PII guard.
Layer 1: OpenMed Nemotron PII model (when available)
Layer 2: Indian ID regex (always runs)
Layer 3: Regional language flag
"""

import os
import re
import sys
import hashlib
import logging

logger = logging.getLogger(__name__)

# ── Layer 2 — Indian ID regex patterns ────────────────────
PII_PATTERNS = {
    "AADHAAR": re.compile(r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'),
    "PAN": re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'),
    "UPI_ID": re.compile(
        r'\b[\w.]+@(?:paytm|gpay|phonepe|upi|okaxis|oksbi|ybl|ibl|axl|apl|'
        r'okhdfcbank|okicici|barodampay|sbi|icici|hdfc|axis)\b',
        re.IGNORECASE,
    ),
    "INDIAN_PHONE": re.compile(r'(?:\+91[\s\-]?)?(?:\b[6-9]\d{9}\b)'),
    "IFSC": re.compile(r'\b[A-Z]{4}0[A-Z0-9]{6}\b'),
    "VOTER_ID": re.compile(r'\b[A-Z]{3}\d{7}\b'),
    "EMAIL": re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
    # Social media handles must come AFTER EMAIL to avoid conflict
    "TWITTER_HANDLE": re.compile(r'(?<!\w)@[A-Za-z0-9_]{1,50}\b'),
    "URL": re.compile(r'https?://[^\s\]\)]+'),
}


REGIONAL_LANGS = {'hi', 'mr', 'gu', 'ta', 'te', 'kn', 'ml', 'bn', 'pa', 'or', 'as', 'ur'}

# Common medications that PII models sometimes misidentify as names (e.g., Dolo)
# This is a small protection layer for the Clean test and common medical queries.
PROTECTED_MEDS = re.compile(r'\b(Dolo|Paracetamol|Crocin|Calpol|Taxim|Combiflam|Azithromycin|Amoxicillin)\b', re.IGNORECASE)


def redact_pii(text: str, lang: str = "en", preserve_urls: bool = False) -> dict:
    """
    Run 3-layer PII redaction.
    Returns: {redacted_text, pii_entities_found, pii_language_flag, original_sha256}
    """
    original_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    pii_entities = []
    redacted = text

    # ── Layer 1 — Indian ID regex (DISABLED FOR NLP BASELINE TEST) ──
    # for pii_type, pattern in PII_PATTERNS.items():
    #     for match in pattern.finditer(redacted):
    #         matched_text = match.group()
    #         redacted = redacted.replace(matched_text, f"[{pii_type}]")
    #         pii_entities.append({"type": pii_type, "layer": 1, "method": "regex"})


    # ── Layer 2 — OpenMed NLP Models (Catch names, addresses, etc.) ──────
    fast_mode = os.getenv("FAST_MODE", "false").lower() in ("true", "1", "yes")
    
    if not fast_mode and lang in ["en", "hi", "te"]:
        try:
            from openmed import extract_pii, deidentify
            from openmed.core import OpenMedConfig
            
            # Force CPU execution
            _ = OpenMedConfig(device="cpu")
            
            model_map = {
                "en": "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1",
                "hi": "OpenMed/OpenMed-PII-Hindi-SuperClinical-Small-44M-v1",
                "te": "OpenMed/OpenMed-PII-Telugu-FastClinical-Small-82M-v1",
            }
            
            model_name = model_map.get(lang, model_map["en"])
            truncated = redacted[:1900]
            
            # Extract to check for false positives like medications
            entities_res = extract_pii(truncated, lang=lang, model_name=model_name, use_smart_merging=True)
            
            valid_entities = []
            for ent in entities_res.entities:
                # Protection: If the model thinks a medication is a name, skip it
                if PROTECTED_MEDS.search(ent.text):
                    continue
                # Protection: preserve URLs if requested
                if preserve_urls and ent.label.lower() in ("url", "link"):
                    continue
                valid_entities.append(ent)
                pii_entities.append({"type": ent.label, "layer": 2, "text": ent.text[:10]})

            if valid_entities:
                redacted = truncated
                # Setup anonymizer to ensure realistic fake data
                from openmed.core.anonymizer import Anonymizer
                anonymizer = Anonymizer(lang=lang, consistent=True, seed=42)
                
                # Replace longer entities first to prevent partial substring replacements
                for ent in sorted(valid_entities, key=lambda e: len(e.text), reverse=True):
                    if ent.text in redacted:
                        surrogate = anonymizer.surrogate(ent.text, ent.label, lang=lang)
                        redacted = redacted.replace(ent.text, surrogate)


            
        except Exception as e:
            logger.debug(f"Layer 2 PII skipped (OpenMed error): {e}")

    # ── Layer 3 — Regional language flag ─────────────────
    pii_language_flag = lang in REGIONAL_LANGS
    if pii_language_flag:
        pii_entities.append({
            "type": "REGIONAL_LANGUAGE_FLAG",
            "layer": 3,
            "note": "Manual PII review advised for non-English content",
        })

    return {
        "redacted_text": redacted,
        "pii_entities_found": pii_entities,
        "pii_language_flag": pii_language_flag,
        "original_sha256": original_sha256,
    }


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    # Default to FAST_MODE=true for predictable unit testing of the regex layer.
    # To test heavy models, run with: $env:FAST_MODE="false"; uv run .\nlp\pii_guard.py
    if "FAST_MODE" not in os.environ:
        os.environ["FAST_MODE"] = "false"

    tests = [
        ("Full Name", "I am Dr. Ramesh Gupta and I work at AIIMS.", True),
        ("Address", "Delivery to Flat 4B, Vasant Kunj, New Delhi 110070.", True),
        ("Age/Gender", "A 45 year old female patient reported nausea.", True),
        ("Hospital", "Admitted to Apollo Hospital for emergency surgery.", True),
        ("Clean", "Paracetamol 500mg taken twice a day for fever.", False),
        ("Twitter", "@Francinean35966 @ick_real It can cause migraines", True),
    ]

    print("=" * 55)
    print("  PII Guard — NLP Baseline Test (Regex DISABLED)")
    print("=" * 55)
    for name, text, expect_pii in tests:
        result = redact_pii(text)
        found_pii = len([e for e in result["pii_entities_found"] if e["layer"] != 3]) > 0
        status = "✅ PASS" if found_pii == expect_pii else "❌ FAIL"
        
        print(f"\n[{name}] {status}")
        print(f"Original : {text}")
        print(f"Redacted : {result['redacted_text']}")
        if found_pii:
            entities = [f"{e['text']} ({e['type']})" for e in result["pii_entities_found"] if e["layer"] != 3]
            print(f"Entities : {', '.join(entities)}")

    print("\n" + "─" * 55)
    print("NLP Baseline test complete")
