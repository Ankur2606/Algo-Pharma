# AlgoPharma User Journey Architecture

This document outlines the end-to-end user journeys for the primary personas interacting with the AlgoPharma Pharmacovigilance platform. It maps the user experience directly to the underlying NLP and Data pipelines.

## 👥 User Personas

1. **Pharmacovigilance (PV) Analyst / Medical Reviewer**
   * **Goal:** Identify, verify, and report adverse drug reactions (ADRs) quickly.
   * **Needs:** Clear dashboards, explainable AI reasoning, easy export to regulatory formats (VigiFlow).
2. **Data Engineer / System Administrator**
   * **Goal:** Maintain data pipelines and system health.
   * **Needs:** Crawler configuration, pipeline monitoring, API management.

---

## 🗺️ User Journey Map (PV Analyst)

```mermaid
journey
    title Pharmacovigilance Analyst - AlgoPharma Journey
    
    section 1. Monitoring & Discovery
      Login to secure portal: 5: Analyst
      View Global Signal Dashboard (Red/Amber/Green bands): 5: Analyst
      Notice a new "Red" spike for a specific drug: 4: Analyst
      
    section 2. Investigation & Triage
      Click into specific drug signal: 5: Analyst
      Review raw (PII-redacted) social media posts: 4: Analyst
      Inspect AI confidence & NLP reasoning trace: 4: Analyst
      Verify extracted Symptoms vs. Drug: 5: Analyst
      
    section 3. Action & Reporting
      Corroborate with thread replies: 4: Analyst
      Validate & Confirm the Adverse Event: 5: Analyst
      Export validated signal to PvPI-formatted CSV: 5: Analyst
      Upload to VigiFlow / Regulatory body: 5: Analyst
```

---

## 🔄 End-to-End System Flow (User Perspective)

```mermaid
sequenceDiagram
    actor User as PV Analyst
    participant UI as AlgoPharma Dashboard
    participant API as Backend API
    participant Pipeline as NLP Pipeline
    participant DB as Graph/SQL DB
    
    User->>UI: Configure New Crawl (e.g., "Paracetamol on Reddit")
    UI->>API: Start Crawl Job
    API->>Pipeline: Trigger Scraper & Ingestion
    Pipeline-->>Pipeline: Step 1: PII Guard (Redaction)
    Pipeline-->>Pipeline: Step 2-5: NER, Sentiment, Negation
    Pipeline-->>Pipeline: Step 6-7: AE Flag & Corroboration
    Pipeline->>DB: Store clean data & reasoning trace
    DB-->>UI: Update PRR/ROR Signals
    
    UI->>User: Alert: New Signal Detected (Amber/Red)
    User->>UI: View Signal Details
    UI->>DB: Fetch Trace & Redacted Posts
    DB-->>UI: Return Explainable AI Data
    User->>UI: Confirm Signal & Export
    UI->>User: Download PvPI CSV File
```

---

## 📝 Step-by-Step Feature Mapping

### Phase 1: Ingestion & Setup
* **User Action:** The user configures a live scraper for specific subreddits or Twitter keywords, or uploads a batch CSV of historical data.
* **System Response:** The system validates the input and begins asynchronous ingestion. The UI shows a progress bar. 

### Phase 2: Processing & PII Protection
* **User Action:** The user waits while the system processes the data.
* **System Response:** Behind the scenes, **Step 1 (PII Guard)** is executed. All patient names, phone numbers, and IDs are stripped. This ensures that when the user eventually sees the text, it is completely anonymized and regulatory compliant.

### Phase 3: Signal Dashboard
* **User Action:** The user logs in and views the main dashboard.
* **System Response:** The UI queries the database for PRR/ROR (Proportional Reporting Ratio) calculations. It displays drugs categorized by risk bands:
  * 🔴 **Red:** Urgent signal, PRR > 2, sudden spike.
  * 🟡 **Amber:** Emerging signal, requires monitoring.
  * 🟢 **Green:** Baseline noise, no action needed.

### Phase 4: Drill-Down & Explainability
* **User Action:** The user clicks on a "Red" signal for a specific drug (e.g., Dolo 650) to see *why* it was flagged.
* **System Response:** The system displays the individual posts. For each post, it highlights:
  * The identified **Drug** (from NER).
  * The identified **Symptom** (from NER).
  * The **Sentiment** (Negative).
  * The **Negation Status** (Confirming the symptom was *not* negated).
  * The **Thread Corroboration Score** (How many replies agree with the OP).

### Phase 5: Export & Compliance
* **User Action:** The user agrees with the AI's assessment, marks the signal as `CONFIRMED`, and clicks "Export to VigiFlow".
* **System Response:** The system generates a pre-formatted CSV matching the Pharmacovigilance Programme of India (PvPI) standards, ready for immediate upload to official regulatory portals.
