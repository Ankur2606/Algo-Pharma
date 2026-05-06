# Algo-Pharma: Project Explanation & Architecture Guide

## 1. What does the project do?
**Algo-Pharma** is a real-time **Pharmacovigilance Social Listening Platform** built for the "AI for Bharat" hackathon. 

When a new medicine is released, pharmaceutical companies and regulators need to monitor public forums to see if people are experiencing **Adverse Events (AE)**—i.e., side effects. Instead of doing this manually, Algo-Pharma automatically crawls platforms like Reddit and Twitter, runs advanced AI (NLP) to detect drugs, symptoms, and negative sentiment, and surfaces statistical **Signals** (alerts) when a specific side-effect spikes in the community.

It features offline JSON processing, a robust 4-gate AI rule engine, an agentic forum scraper for non-standard medical forums, and regional Indian language support via Sarvam AI.

---

## 2. Architecture: How the Files Stitch Together

The codebase is built on **Python 3.12** using `uv` for package management, **FastAPI** for the backend API, **SQLAlchemy (SQLite)** for the database, and **HuggingFace + spaCy** for the AI pipelines.

### The Pipeline Flow
1. **Data Ingestion (Crawlers & Tasks)**
   - `reddit_crawler.py` & `twitter_crawler.py` run independently to scrape raw social media posts into local `.json` files.
   - `tasks/ingest_existing.py` reads these JSON files and pushes each post into the NLP pipeline.
2. **The NLP Processing Pipeline (`nlp/` folder)**
   - **`pii_guard.py`**: First, it strips out Personally Identifiable Information (Aadhaar, PAN, phone numbers) so patient privacy is maintained.
   - **`ner_pipeline.py`**: Extracts **Drugs** (e.g., Dolo 650) and **Symptoms** (e.g., Nausea) using OpenMed HuggingFace models.
   - **`sentiment.py`**: Evaluates if the post is NEGATIVE, POSITIVE, or NEUTRAL. (If it's an Indian regional language, it uses **Sarvam AI** to translate it to English first).
   - **`negation.py`**: Uses `spaCy` to ensure the user isn't saying *"I did **NOT** have nausea"*.
   - **`ae_detector.py`**: The Rule Engine. It flags a post as an Adverse Event ONLY IF: 
     *(Drug Found) AND (Symptom Found) AND (Sentiment is Negative) AND (Symptom is not negated)*.
   - **`thread_scorer.py`**: Looks at the comments/replies of the post to corroborate the side-effect (boosting confidence).
3. **Signal Detection (`nlp/signal_detector.py`)**
   - It aggregates all the flagged AE posts in the database.
   - If it sees a statistical spike (e.g., "Dolo 650" + "Nausea" appearing frequently together), it calculates the **PRR (Proportional Reporting Ratio)** and generates a formal **Signal**.
4. **Agentic Forum Onboarding (`agentic/forum_onboarding.py`)**
   - A unique feature where an admin can paste *any* unknown medical forum URL. The system uses **Firecrawl** and **Google Gemini 3.0** to automatically figure out the website's structure and generate a custom scraper on the fly.
5. **The API Layer (`api/` & `main.py`)**
   - Exposes the database and signals to the frontend via standard FastAPI endpoints.

---

## 3. How to Run the Demos

You have two primary ways to run the project for judges or testing.

### A. The "Seed Demo" (`seed_demo_data.py` / `demo.py`)
**What it means:** A "Seed Demo" runs the entire pipeline locally from start to finish using the offline `.json` files already generated. It simulates the backend processing without requiring the API server to be running.
**Why use it:** It's the safest and fastest way to show judges that the AI pipeline works perfectly without worrying about live API rate limits, slow network connections, or missing data.

**How to run it:**
```bash
# This creates the DB, ingests the JSON files, runs the NLP pipeline, 
# detects signals, and prints a beautiful terminal summary.
uv run python seed_demo_data.py
```
*(You can also use `uv run python demo.py` for a similar CLI-based pipeline demonstration).*

### B. The "Realistic Demo" (`main.py` + Live Crawlers)
**What it means:** This simulates the actual production environment. You run the backend server, trigger live scraping, and view the API responses.

**How to run it:**
1. Start the FastAPI server:
   ```bash
   uv run python main.py
   ```
2. Open your browser to `http://localhost:8000/docs`. This gives you the Swagger UI.
3. You can test endpoints here (e.g., fetching signals, adding projects).
4. **Trigger Live Data:** In a separate terminal, run a live crawler:
   ```bash
   uv run python twitter_crawler.py
   ```
5. Trigger the ingestion endpoint `/api/crawl/trigger/{project_id}` via the Swagger UI to process the new data.

---

## 4. How to Test Each Module

Every core file in this project is built to be **standalone**. They all contain an `if __name__ == "__main__":` block at the bottom. This means you don't need a massive testing framework to see how a specific AI piece works—you just run the file directly.

**Examples of testing individual components:**

- **Test PII Redaction** (Watch it hide Aadhaar/PAN cards):
  ```bash
  uv run python nlp/pii_guard.py
  ```
- **Test Negation** (Watch it differentiate "I had nausea" vs "I had no nausea"):
  ```bash
  uv run python nlp/negation.py
  ```
- **Test Sentiment & Translation**:
  ```bash
  uv run python nlp/sentiment.py
  ```
- **Test the Agentic Forum Scraper** (Ensure `FIRECRAWL_API_KEY` and `GEMINI_API_KEY` are in `.env`):
  ```bash
  uv run python agentic/forum_onboarding.py
  ```
- **Run the Master Test Suite**:
  This runs an integration check across all 12 core tests to ensure the whole system is healthy.
  ```bash
  uv run python test_pipeline.py
  ```

> **Pro-Tip: The `FAST_MODE` Toggle**
> In your `.env` file, there is a `FAST_MODE=false` flag. If your laptop is struggling to load the heavy HuggingFace AI models during the presentation, change this to `FAST_MODE=true`. The system will instantly bypass HuggingFace and use lightweight Keyword Matching + VADER sentiment to keep the demo running lightning fast!
