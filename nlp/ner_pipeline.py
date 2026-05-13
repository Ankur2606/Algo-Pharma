"""
AlgoPharma — Drug + Symptom NER pipeline.
Two-model NER (when available) with keyword boost fallback.
"""

import re
import sys
import os
from pathlib import Path

# Add project root to sys.path for standalone script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging

logger = logging.getLogger(__name__)

# ── Indian pharma drug keywords ──────────────────────────
DRUG_KEYWORDS = [
    "dolo 650", "dolo", "paracetamol 650mg", "paracetamol", "crocin",
    "combiflam", "brufen", "ibuprofen", "azithromycin", "metformin",
    "amoxicillin", "aspirin", "cetirizine", "montair lc", "allegra",
    "pan 40", "omeprazole", "metronidazole", "ciprofloxacin",
    "telmisartan", "amlodipine", "atorvastatin", "losartan",
    "hydroxychloroquine", "ivermectin", "remdesivir", "favipiravir",
    "calpol", "saridon", "disprin", "aceclofenac", "diclofenac",
    "pantoprazole", "rabeprazole", "ranitidine", "domperidone",
    "ondansetron", "levocetirizine", "montelukast", "doxycycline",
    "amoxyclav", "cefixime", "ofloxacin", "norfloxacin",
]

# ── Symptom keywords ────────────────────────────────────
SYMPTOM_KEYWORDS = [
    "nausea", "vomiting", "headache", "fever", "dizziness",
    "stomach pain", "abdominal pain", "liver pain", "rash",
    "itching", "allergic reaction", "fatigue", "weakness", "diarrhea",
    "constipation", "chest pain", "breathing difficulty", "swelling",
    "palpitation", "anxiety", "insomnia", "drowsiness", "hair loss",
    "weight gain", "weight loss", "acidity", "gastritis", "ulcer",
    "bleeding", "jaundice", "dark urine", "loss of appetite",
    "skin discoloration", "muscle pain", "joint pain", "back pain",
    "kidney pain", "burning sensation", "tingling", "numbness",
    "diarrhoea", "vomit", "dizzy", "tired", "sleepy", "sleepless",
    "stomach ache", "body pain", "loose motion", "loose motions",
    "gas", "bloating", "acid reflux", "skin rash", "liver damage",
    "liver failure", "kidney failure", "overdose",
]

# Sort by length descending so multi-word matches take priority
DRUG_KEYWORDS.sort(key=len, reverse=True)
SYMPTOM_KEYWORDS.sort(key=len, reverse=True)


def _keyword_search(text: str, keywords: list[str], already_found: set) -> list[dict]:
    """Find keywords in text that weren't already found by model."""
    results = []
    text_lower = text.lower()
    for kw in keywords:
        if kw.lower() in already_found:
            continue
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        for match in pattern.finditer(text_lower):
            results.append({
                "text": kw,
                "score": 0.90,
                "start": match.start(),
                "end": match.end(),
                "source": "keyword",
            })
            already_found.add(kw.lower())
            break  # one match per keyword is sufficient
    return results


def _merge_subwords(raw_entities: list[dict], text: str) -> list[dict]:
    """Merge adjacent subword tokens based on start/end indices to fix broken aggregation."""
    if not raw_entities:
        return []
        
    sorted_ents = sorted([e for e in raw_entities if e.get("score", 0) > 0.60], key=lambda x: x.get("start", 0))
    if not sorted_ents:
        return []
        
    merged = []
    current = sorted_ents[0].copy()
    
    for i in range(1, len(sorted_ents)):
        ent = sorted_ents[i]
        # Merge if they are adjacent or separated by a single space/punctuation
        if ent.get("start", 0) <= current.get("end", 0) + 1:
            current["end"] = max(current["end"], ent.get("end", 0))
            current["score"] = min(current["score"], ent.get("score", 0))
        else:
            merged.append(current)
            current = ent.copy()
            
    merged.append(current)
    
    # Extract clean text from the original string using the merged indices
    for m in merged:
        m["word"] = text[m["start"]:m["end"]].strip()
        
    return merged


def extract_entities(text: str) -> dict:
    """
    Extract drugs and symptoms from text.
    Returns: {"drugs": [...], "symptoms": [...]}
    Each entity: {text, score, start, end, source}
    """
    from nlp.models_loader import get_models
    models = get_models()

    drugs = []
    symptoms = []
    found_drugs = set()
    found_symptoms = set()

    truncated = text[:512]

    # ── Model-based NER (when available) ──────────────────
    drug_ner = models.get("drug_ner")
    if drug_ner is not None:
        try:
            raw = drug_ner(truncated)
            merged = _merge_subwords(raw, truncated)
            for ent in merged:
                ent_text = ent.get("word", "")
                # Skip very short tokens (e.g. "B4", "Ye") — not real drug names
                if ent_text and len(ent_text) >= 3 and ent_text.lower() not in found_drugs:
                    drugs.append({
                        "text": ent_text,
                        "score": round(float(ent["score"]), 4),
                        "start": ent.get("start", 0),
                        "end": ent.get("end", 0),
                        "source": "model",
                    })
                    found_drugs.add(ent_text.lower())
        except Exception as e:
            logger.warning(f"Drug NER model error: {e}")

    disease_ner = models.get("disease_ner")
    if disease_ner is not None:
        try:
            raw = disease_ner(truncated)
            merged = _merge_subwords(raw, truncated)
            for ent in merged:
                ent_text = ent.get("word", "")
                # Skip very short tokens — not real symptom names
                if ent_text and len(ent_text) >= 3 and ent_text.lower() not in found_symptoms:
                    symptoms.append({
                        "text": ent_text,
                        "score": round(float(ent["score"]), 4),
                        "start": ent.get("start", 0),
                        "end": ent.get("end", 0),
                        "source": "model",
                    })
                    found_symptoms.add(ent_text.lower())
        except Exception as e:
            logger.warning(f"Disease NER model error: {e}")

    # ── Keyword boost (always runs) ──────────────────────
    drugs.extend(_keyword_search(text, DRUG_KEYWORDS, found_drugs))
    symptoms.extend(_keyword_search(text, SYMPTOM_KEYWORDS, found_symptoms))

    return {"drugs": drugs, "symptoms": symptoms}


# ── Self-test ─────────────────────────────────────────────
if __name__ == "__main__":
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

    import os
    os.environ["FAST_MODE"] = "false"

    tests = [
        "I took Dolo 650 and got severe nausea and headache",
        "paracetamol caused stomach pain and vomiting for me",
        "after taking combiflam I had dizziness and rash",
    ]

    print("=" * 55)
    print("  NER Pipeline — Self-test")
    print("=" * 55)
    all_pass = True
    for text in tests:
        result = extract_entities(text)
        has_drug = len(result["drugs"]) > 0
        has_symptom = len(result["symptoms"]) > 0
        ok = has_drug and has_symptom
        if not ok:
            all_pass = False
        drug_names = [d["text"] for d in result["drugs"]]
        symp_names = [s["text"] for s in result["symptoms"]]
        print(f"  {'✅' if ok else '❌'} \"{text[:50]}...\"")
        print(f"       Drugs: {drug_names}  |  Symptoms: {symp_names}")

    print("─" * 55)
    print(f"{'✅' if all_pass else '❌'} ner_pipeline self-test {'PASS' if all_pass else 'FAIL'}")
