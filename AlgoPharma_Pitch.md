# 🚀 AlgoPharma: Agentic Pharmacovigilance OS
## Live Demo Pitch & Script

### 🌟 The Vision
AlgoPharma replaces manual, slow safety signal detection with an autonomous, real-time intelligence pipeline. By coupling Groq-accelerated LLM query routing with an asynchronous Celery/FastAPI architecture, the platform dynamically scrapes and processes live social streams. 

Our **Agentic Acquisition Engine** combined with a **5-Stage Clinical NLP Pipeline (OpenMed, RoBERTa, spaCy)** ruthlessly eliminates noise to autonomously surface high-density drug-symptom safety signals directly to our zero-code glassmorphic dashboard.

---

### 🎬 Demo Scenario 1: Live Reddit Surveillance (The "Known Source" Flow)

**The Goal:** Demonstrate AlgoPharma's ability to pull live, unstructured social data from Reddit and immediately process it through our strict clinical NLP gates.

**The Script:**
1. **The Setup:** "We want to track adverse events for **Ibuprofen** on Reddit. Traditionally, pharmacovigilance teams wait for FDA FAERS reports, which are months delayed. Let's see what people are saying *today*."
2. **The Action:** In the Chat interface, we ask: 
   > *"Find recent discussions about Ibuprofen on Reddit."*
3. **The Agentic Routing:** The Groq-powered Chat Manager identifies the `reddit` source and the `Ibuprofen` entity. It enforces the slots and triggers the `READY` signal.
4. **The Pipeline (Behind the Scenes):** 
   - The FastApi endpoint accepts the request and immediately offloads the heavy lifting to our decoupled **Celery worker**.
   - The `reddit_crawler` executes, scraping live posts using stealth bot configurations.
   - Posts are pushed through the **4-Gate Clinical Integrity check**: OpenMed-validated entities, RoBERTa sentiment, and spaCy negation detection.
5. **The Reveal (Dashboard):** We navigate to the Intelligence Dashboard. We see the real-time processing metrics update. The Relational Risk map dynamically builds drug-symptom graphs (e.g., Ibuprofen → stomach pain), surfacing high-density safety signals instantly.

---

### 🪄 Demo Scenario 2: Zero-Code Forum Onboarding (The "Agentic Magic")

**The Goal:** Demonstrate our true novelty—the ability to dynamically ingest data from *any* custom patient forum without writing a single line of crawler code. 

**The Script:**
1. **The Setup:** "Reddit is great, but the most severe and detailed adverse events are often discussed in niche, specialized patient forums. Building custom scrapers for every new forum is a massive, expensive bottleneck for pharma companies."
2. **The Action:** In the Chat interface, we provide a custom forum URL:
   > *"Monitor discussions for this drug on this specific patient forum URL..."*
3. **The Agentic Routing:** The Chat Manager detects a custom URL and triggers the **Agentic Forum Onboarding** workflow.
4. **The Pipeline (Behind the Scenes):**
   - *This is the zero-code magic.* The Agentic Onboarding system (`forum_onboarding.py`) uses advanced LLMs to autonomously fetch and analyze the forum's raw HTML/DOM structure.
   - It intelligently reverse-engineers the website to identify the exact CSS selectors for post titles, body text, authors, timestamps, and pagination buttons.
   - It dynamically generates an **Apify Actor configuration** payload and automatically initiates the serverless cloud crawl.
5. **The Reveal (Dashboard):** A previously unmonitored, unsupported website has been completely mapped, scraped, and pushed through our Clinical NLP pipeline in minutes, with zero developer intervention. The dashboard now displays highly niche, newly identified safety signals.

---

### 📈 The Value Proposition for Judges
- **Speed:** From months of FAERS reporting delays to real-time signal detection.
- **Reach (The Novelty):** Moving beyond standard APIs to the deep web of patient forums using autonomous **Agentic Onboarding**.
- **Integrity:** Our 4-Gate NLP system ensures that only highly confident, relational signals make it to the dashboard, drastically reducing false positives (addressing the "noisy data" problem in pharmacovigilance).

***"AlgoPharma doesn't just search data; it autonomously learns how to acquire it, process it, and map the risk."***
