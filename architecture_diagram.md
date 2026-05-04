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
║  │  1A. OpenMed/privacy-filter-nemotron                │    ║
║  │      → 55 clinical entities: MRN, health_plan_ID,   │    ║
║  │        blood_type, names, email, phone, DOB          │    ║
║  │      → F1: 0.993 on medical_record_number           │    ║
║  │      → F1: 0.995 on health_plan_beneficiary_number  │    ║
║  │                                                     │    ║
║  │  1B. Indian Regex Layer                             │    ║
║  │      → Aadhaar, PAN, UPI, IFSC, IN-phone           │    ║
║  │                                                     │    ║
║  │  1C. Hindi/Telugu: OpenMed multilingual models      │    ║
║  │                                                     │    ║
║  │  OUTPUT: Redacted text + PII audit log              │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 2 — DRUG NER                                   │    ║
║  │  OpenMed-NER-PharmaDetect-BigMed-278M               │    ║
║  │  → Detects: Dolo 650, Paracetamol, brand names      │    ║
║  │  → Trained on BC5CDR chemical corpus                │    ║
║  │  → Maps to MedDRA standard drug codes               │    ║
║  └─────────────────────────────────────────────────────┘    ║
║         ↓                                                    ║
║  ┌─────────────────────────────────────────────────────┐    ║
║  │ STEP 3 — SYMPTOM/DISEASE NER                        │    ║
║  │  OpenMed-NER-DiseaseDetect-BioMed-335M              │    ║
║  │  → Detects: nausea, stomach pain, liver discomfort  │    ║
║  │  → Trained on BC5CDR disease corpus                 │    ║
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
║  │  Spike detection: today > 2× 7-day rolling avg      │    ║
║  │  PRR ≥ 2 AND chi-square ≥ 4 AND count ≥ 3          │    ║
║  │  → SIGNAL created with full audit trail             │    ║
║  │  → Alert: email / webhook / Slack MCP               │    ║
║  │  → Dashboard: GREEN / AMBER / RED band              │    ║
║  │  → Export: PvPI-formatted CSV for VigiFlow upload   │    ║
║  └─────────────────────────────────────────────────────┘    ║
╚══════════════════════════════════════════════════════════════╝