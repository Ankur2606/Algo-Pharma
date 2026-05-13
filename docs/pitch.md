# for agentic forum onboarding :

Our onboarding is Privacy-by-Design. We detect the forum language immediately after scraping, then apply language-specific PII redaction before any data leaves our server — whether going to an LLM for structure analysis, a translation API like Sarvam, or sample extraction. A Hindi forum gets the 44M Hindi model; Telugu gets the 82M Telugu model. The translation API only ever sees anonymised content.

---