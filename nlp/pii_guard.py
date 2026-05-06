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
import torch

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
}

REGIONAL_LANGS = {'hi', 'mr', 'gu', 'ta', 'te', 'kn', 'ml', 'bn', 'pa', 'or', 'as', 'ur'}


def redact_pii(text: str, lang: str = "en") -> dict:
    """
    Run 3-layer PII redaction.
    Returns: {redacted_text, pii_entities_found, pii_language_flag, original_sha256}
    """
    original_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
    pii_entities = []
    redacted = text

    # ── Layer 1 — OpenMed Nemotron PII model ─────────────
    try:
        from nlp.models_loader import get_models
        models = get_models()
        pii_model = models.get("pii_model")
        pii_tokenizer = models.get("pii_tokenizer")

        if pii_model is not None and pii_tokenizer is not None:
            truncated = text[:512]
            inputs = pii_tokenizer(truncated, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = pii_model(**inputs)

            predictions = torch.argmax(outputs.logits, dim=-1)[0]
            tokens = pii_tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            labels = [pii_model.config.id2label.get(p.item(), "O") for p in predictions]

            current_entity = None
            current_tokens = []
            for token, label in zip(tokens, labels):
                if token in ("[CLS]", "[SEP]", "[PAD]"):
                    continue
                if label.startswith("B-"):
                    if current_entity and current_tokens:
                        etype = current_entity.split("-", 1)[-1]
                        entity_text = pii_tokenizer.convert_tokens_to_string(current_tokens).strip()
                        if entity_text and entity_text in redacted:
                            redacted = redacted.replace(entity_text, f"[{etype.upper()}]", 1)
                            pii_entities.append({"type": etype, "layer": 1})
                    current_entity = label
                    current_tokens = [token]
                elif label.startswith("I-") and current_entity:
                    current_tokens.append(token)
                else:
                    if current_entity and current_tokens:
                        etype = current_entity.split("-", 1)[-1]
                        entity_text = pii_tokenizer.convert_tokens_to_string(current_tokens).strip()
                        if entity_text and entity_text in redacted:
                            redacted = redacted.replace(entity_text, f"[{etype.upper()}]", 1)
                            pii_entities.append({"type": etype, "layer": 1})
                    current_entity = None
                    current_tokens = []
            # flush last entity
            if current_entity and current_tokens:
                etype = current_entity.split("-", 1)[-1]
                entity_text = pii_tokenizer.convert_tokens_to_string(current_tokens).strip()
                if entity_text and entity_text in redacted:
                    redacted = redacted.replace(entity_text, f"[{etype.upper()}]", 1)
                    pii_entities.append({"type": etype, "layer": 1})
    except Exception as e:
        logger.debug(f"Layer 1 PII skipped: {e}")

    # ── Layer 2 — Indian ID regex (always runs) ──────────
    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(redacted):
            matched_text = match.group()
            redacted = redacted.replace(matched_text, f"[{pii_type}]", 1)
            pii_entities.append({"type": pii_type, "layer": 2})

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

    import os
    os.environ["FAST_MODE"] = "true"  # skip heavy model for self-test

    tests = [
        ("Aadhaar", "My aadhaar is 1234 5678 9012", "[AADHAAR]"),
        ("PAN", "PAN card ABCDE1234F is mine", "[PAN]"),
        ("Email", "Reach me at test@gmail.com for info", "[EMAIL]"),
        ("Phone", "Call me at +91 9876543210", "[INDIAN_PHONE]"),
        ("Clean", "Dolo 650 gave me nausea and headache", None),
    ]

    print("=" * 55)
    print("  PII Guard — Self-test")
    print("=" * 55)
    all_pass = True
    for name, text, expect_tag in tests:
        result = redact_pii(text)
        if expect_tag:
            ok = expect_tag in result["redacted_text"]
        else:
            ok = len([e for e in result["pii_entities_found"] if e["layer"] != 3]) == 0
        status = "✅ PASS" if ok else "❌ FAIL"
        if not ok:
            all_pass = False
        print(f"  {name:12s} {status}  →  {result['redacted_text'][:60]}")

    print("─" * 55)
    print(f"{'✅' if all_pass else '❌'} pii_guard self-test {'PASS' if all_pass else 'FAIL'}")
