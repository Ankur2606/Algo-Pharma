╔══════════════════════════════════════════════════════════════╗
║              ALGOPHARMA — FULL NLP PIPELINE                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  RAW POST (Reddit / Twitter / Forum)                         ║
║         ↓                                                    ║
║  [STEP 0] Language Detection (langdetect)                    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 1 — PII GUARD (runs FIRST, always)             │    ║
║  │                                                     │    ║
║  │  1A. OpenMed-PII-SuperClinical-Small-44M-v1         │    ║
║  │      → English clinical de-identification           │    ║
║  │                                                     │    ║
║  │  1B. Indian Regex Layer                             │    ║
║  │      → Aadhaar, PAN, UPI, IFSC, IN-phone           │    ║
║  │                                                     │    ║
║  │  1C. Hindi/Telugu PII Models                        │    ║
║  │      → OpenMed-PII-Hindi-SuperClinical (44M)        │    ║
║  │      → OpenMed-PII-Telugu-FastClinical (82M)        │    ║
║  │                                                     │    ║
║  │  OUTPUT: Redacted text + PII audit log              │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 2 — DRUG NER                                   │    ║
║  │  OpenMed-NER-PharmaDetect-ModernClinical-149M       │    ║
║  │  → Detects: Dolo 650, Paracetamol, brand names      │    ║
║  │  → CPU-friendly, 149M params                        │    ║
║  │  → Maps to MedDRA standard drug codes               │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 3 — SYMPTOM/DISEASE NER                        │    ║
║  │  OpenMed-NER-DiseaseDetect-SuperClinical-184M       │    ║
║  │  → Detects: nausea, stomach pain, liver discomfort  │    ║
║  │  → CPU-friendly, 184M params                        │    ║
║  │  → Maps to MedDRA preferred terms                   │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 4 — SENTIMENT SCORING                          │    ║
║  │  cardiffnlp/twitter-roberta-base-sentiment          │    ║
║  │  → Trained on 58M real tweets                       │    ║
║  │  → Understands "my tummy is killing me"             │    ║
║  │  → Output: POSITIVE / NEGATIVE / NEUTRAL + score   │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 5 — NEGATION DETECTION                         │    ║
║  │  medspaCy clinical negation                         │    ║
║  │  → "no nausea" → symptom negated → not AE          │    ║
║  │  → "denied stomach pain" → not AE                   │    ║
║  │  → Rule-based, fully explainable                    │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 6 — AE FLAG RULE ENGINE                        │    ║
║  │  IF drug_found AND symptom_found                    │    ║
║  │     AND sentiment==NEGATIVE                         │    ║
║  │     AND NOT all_symptoms_negated                    │    ║
║  │  → AE_FLAG = True                                   │    ║
║  │  → confidence = sentiment_score × 0.9               │    ║
║  │  → Full reasoning trace stored for audit            │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 7 — THREAD CORROBORATION                       │    ║
║  │  All replies run through Steps 2-6 independently    │    ║
║  │  corroboration_score = confirming_replies/total     │    ║
║  │  final_confidence = (ae_conf×0.60)                  │    ║
║  │                   + (corroboration×0.25)            │    ║
║  │                   + (source_health×0.15)            │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 8 — PRR/ROR SIGNAL DETECTION                   │    ║
║  │  Disproportionality analysis for adverse events     │    ║
║  │  → STRONG/MODERATE: PRR ≥ 2 AND χ² ≥ 4 AND count ≥ 3│    ║
║  │  → MODERATE: PRR ≥ 1.5 AND count ≥ 2                │    ║
║  │  → WEAK: count ≥ 1 (co-occurrence)                  │    ║
║  │  → Dashboard: GREEN / AMBER / RED band              │    ║
║  │  → Export: PvPI-formatted CSV for VigiFlow upload   │    ║
║  └─────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════╝