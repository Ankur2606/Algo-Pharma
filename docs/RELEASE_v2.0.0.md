# AlgoPharma v2.0.0 Release Notes

## 🚀 Major Pipeline & Architectural Upgrades

### 1. PII Redaction Architecture Hardened
- **URL Hallucination Solved (`nlp/pii_guard.py`)**: Implemented a `preserve_urls=True` flag to prevent the PII model from replacing real forum links with fake ones (e.g., `johnson-king.com`).
- **Bypassed OpenMed `deidentify`**: Rewrote the core loop to manually apply synthetic surrogates strictly to names/phone numbers. URLs are now 100% preserved for LLM extraction while keeping patient data masked.
- **Multilingual Edge Protection**: Deployed OpenMed-PII-SuperClinical-Small-44M (English/Hindi) and an 82M variant for Telugu to ensure data privacy natively in the user's language before downstream processing.

### 2. Agentic Forum Pipeline Overhauled
- **Fixed "0 Samples" Truncation Bug (`agentic/forum_onboarding.py`)**: Vastly increased Markdown truncation limits from 5,000 to 15,000 (scraping) and 6,000 to 25,000 (LLM Prompting). This ensures actual thread posts are analyzed instead of just the site's navigation bar.
- **Smarter LLM Extraction Prompt**: Explicitly instructed Nvidia Nemotron to fallback to semantic extraction if expected CSS classes are missing in the scraped Markdown.
- **Terminal Visibility**: Added `logger.info` outputs to `_trace_log` for live terminal monitoring of exact pipeline steps without needing to tail `pipeline_trace.log`.
- **Pipeline Documentation**: Rewrote the `onboard_forum` docstring to accurately map out the modern 10-step pipeline.

### 3. Dashboard Integration & Status Fixes
- **Dashboard All-Zeros Bug**: The API previously returned `counts.processed_posts` nested, but the frontend read top-level keys, causing JS to coerce stats to `0`. Fixed to ensure seamless rendering.
- **Status Race Condition Solved (`api/results.py`)**: Introduced sentinel file system (`logs/done_flags/{project_id}.done`). The polling endpoint only marks status "complete" when this file exists, preventing premature frontend loading states.
- **Log File Spam & Reload Loop Fix**: Prevented `_save_result_log()` from spamming files on every poll. Added `--reload-exclude "logs"` to uvicorn to prevent infinite reload loops.
- **Infographic Resilience (`static/index.html`)**: Added three new infographic panels (AE Gate Analysis, Top Drugs, Top Symptoms). Wrapped chart rendering in try-catch blocks to prevent UI crashes if data is missing.

### 4. Pharmacovigilance NLP Tuning
- **CPU-Optimized NER Models**: Swapped massive ~300M parameter models for `ModernClinical-149M` (Drug) and `SuperClinical-184M` (Symptom), providing lightning-fast inference on standard CPUs without sacrificing medical extraction accuracy.
- **Relaxed Signal Thresholds**: Shifted from strict statistical rules to a tiered alerting system (STRONG, MODERATE, WEAK). `MODERATE` triggers at PRR ≥ 1.5 AND count ≥ 2; `WEAK` triggers on any co-occurrence, mimicking real-world early-warning monitoring.
- **False Positive Reduction (`tasks/ingest_existing.py`)**: Drug hints now only inject when the drug name actually appears in the text. Added a `len(ent_text) >= 3` filter to stop noise tokens (e.g., "B4") from being tagged as drugs.
- **Clinical Context Gatekeeper Setup (`architecture.md`)**: Documented the limitation of metaphorical queries (e.g., "chest piece hurt" for tattoos) getting flagged as Adverse Events, setting the stage for a future Clinical Context Classifier.

---
**Version:** 2.0.0  
**Status:** Stable for Hackathon Demonstration
