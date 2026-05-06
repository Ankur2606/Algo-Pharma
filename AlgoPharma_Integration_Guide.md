# AlgoPharma: Integration & Handoff Guide

This document summarizes the recent architectural changes, bug fixes, and feature implementations in the AlgoPharma pipeline. It also provides specific integration guidelines for the frontend and database teams.

---

## 1. Overview of Recent Implementations

Over the last few commits, the core pharmacovigilance pipeline was stabilized and integrated with an agentic chat interface and asynchronous Celery workers. 

### Key Features & Fixes
* **Agentic Chatbot (Slot-Filling):** 
  * Implemented a stateless chat manager (`agentic/chat_manager.py`) that uses **Groq** (`llama-3.3-70b-versatile`) for ultra-fast slot filling.
  * It gathers mandatory fields (`medicine`, `source`) and optional fields (`symptom`) before automatically triggering the backend NLP pipeline.
* **Decoupled Asynchronous Pipeline:**
  * **Phase 1 (Ingestion):** Crawlers (Reddit/Twitter) now fetch data and immediately save it to the DB as `RawPost` records without blocking the API.
  * **Phase 2 (NLP):** A new Celery task (`task_process_unprocessed`) picks up `RawPost` entries that haven't been processed yet, translates them, redacts PII, and runs NER, Sentiment, and AE (Adverse Event) detection.
* **Pipeline Bug Fixes:**
  * **Medicine Hint Injection:** Previously, if the NER model didn't recognize a brand name in a post, the pipeline flagged it as `no_drug` and skipped AE detection. Now, the queried medicine name is injected as a fallback drug entity, ensuring signals are generated even for unknown drugs or slightly off-topic forum posts.
  * **Signal Detection:** Fixed the pipeline to *always* run signal detection after processing, ensuring the dashboard correctly reaches the "complete" state.
* **Live Polling Dashboard:** 
  * Added robust polling logic to the `/api/results/{id}` endpoint and `index.html` to track the pipeline status (`crawling` → `analysing` → `complete`).

---

## 2. Frontend Integration Guide (For Bhavya)

Bhavya, your goal is to build out the React/Next.js frontend. You can use the vanilla JS implementation in `static/index.html` as your primary reference for API contracts and state management.

### The Chat Flow (`/api/chat`)
The chatbot is stateless. You must maintain the `state` object on the frontend and send it back with every message.
* **Endpoint:** `POST /api/chat`
* **Request Body:**
  ```json
  {
    "message": "User's text input",
    "state": {
      "medicine": null,
      "source": null,
      "symptom": null
    }
  }
  ```
* **Behavior:** The API will return an updated `state` and a `bot_message`.
* **Trigger:** When the API returns a `bot_message` of exactly `"READY"`, it means the backend has started the crawling and NLP jobs. The API will also return a `project_id`. You should then transition the user to the Dashboard view and start polling for results.

### The Dashboard Polling Flow (`/api/results/{project_id}`)
Once you have a `project_id`, poll the results endpoint every ~4 seconds.
* **Endpoint:** `GET /api/results/{project_id}`
* **Response:** Contains `status`, `total_raw`, `processed`, `signals`, and lists of processed posts.
* **Statuses to handle:**
  * `"crawling"`: Show a spinner indicating data is being fetched from the sources.
  * `"analysing"`: Show NLP progress (e.g., `data.processed` out of `data.total_raw` posts completed).
  * `"complete"`: Stop polling and render the final Adverse Event signals and charts.
* **Reference:** Look at the `pollResults()` function in `static/index.html` for the timeout (max 5 mins) and stop-condition logic.

---

## 3. Database & Backend Integration Guide (For Astha)

Astha, your goals are to migrate the database to PostgreSQL and build rich analytical dashboards based on the extracted pharmacovigilance data.

### Database Migration (SQLite to PostgreSQL)
The codebase currently uses **SQLAlchemy 2.0** with SQLite (`algopharma.db`). 
* **Schema Reference:** Look at `models.py`. It defines the 12-table schema.
* **Migration Steps:**
  1. Change the `DATABASE_URL` in the `.env` file to your Postgres connection string (e.g., `postgresql://user:pass@localhost/algopharma`).
  2. Because we use SQLAlchemy ORM, the table creation (`Base.metadata.create_all`) should work out-of-the-box with Postgres.
  3. **Note on JSON fields:** In `models.py`, fields like `entities_json`, `sentiment_json`, and `negation_json` are currently stored as `String` (Text) because SQLite has limited JSON support. For Postgres, you can safely upgrade these columns in `models.py` to use SQLAlchemy's native `JSON` or `JSONB` types for better querying performance in your dashboards.

### Dashboard Data Sources
To build the "nice dashboards", you will primarily query these tables (defined in `models.py`):
1. **`Project` table:** Represents a single search session. Contains the target medicine and source.
2. **`ProcessedPost` table:** This is the goldmine for charts.
   * `ae_flag` (Boolean): Was an adverse event detected?
   * `ae_confidence` (Float): Confidence score of the AE.
   * `sentiment_json`: Contains positivity/negativity scores.
   * `entities_json`: Contains extracted `drugs` and `symptoms`.
3. **`Signal` table:** Contains the aggregated statistical signals.
   * `prr_score` (Proportional Reporting Ratio)
   * `ror_score` (Reporting Odds Ratio)
   * Plotting `prr_score` vs. `symptom` name is the primary pharmacovigilance chart.

### Endpoint Behaviors
If you need to build custom dashboard endpoints, follow the pattern in `api/results.py`. It demonstrates how to join the `Project`, `RawPost`, `ProcessedPost`, and `Signal` tables to aggregate statistics safely.
