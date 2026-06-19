import { useState, useEffect, useRef } from "react";
import { Link } from "react-router";

const ARTIFACTS = [
  { file: "/artifacts/System_Architecture.png", title: "System Architecture", desc: "End-to-end view of how data flows from social platforms through the AI pipeline to the signal dashboard." },
  { file: "/artifacts/API_Flow_Architecture.png", title: "API Flow Architecture", desc: "How the FastAPI backend orchestrates chat, crawling, NLP, and result polling across the full stack." },
  { file: "/artifacts/Processing_Pipeline_Architecture.png", title: "NLP Processing Pipeline", desc: "The 8-stage NLP funnel: language detection, PII redaction, drug NER, symptom NER, sentiment, negation, AE flagging, and signal scoring." },
  { file: "/artifacts/Pipeline_Flow_Operational_Runtime.png", title: "Operational Runtime Flow", desc: "How Celery workers asynchronously consume raw posts from Upstash Redis and push results back to the database." },
  { file: "/artifacts/DB_Model_Architecture_Layered.png", title: "Database Model", desc: "The 12-table SQLAlchemy schema covering Projects, Sources, RawPosts, ProcessedPosts, Signals, and audit logs." },
  { file: "/artifacts/Main_Data_Entity_Architecture.png", title: "Data Entity Architecture", desc: "Entity relationships between the core data models — from a raw social post all the way to a ranked pharmacovigilance signal." },
  { file: "/artifacts/Forum_Onboarding_Architecture_Agentic.png", title: "Agentic Forum Onboarding", desc: "How an admin can paste any forum URL and the AI auto-generates a working crawler config using Firecrawl and Groq." },
];

const FEATURES = [
  { icon: "🔍", title: "Agentic Crawling", desc: "Type a natural language query. Groq's Llama 3.3 70B picks the right crawler and extracts data from Reddit, Twitter, or any forum automatically." },
  { icon: "🛡️", title: "Privacy First", desc: "OpenMed PII models (44M/82M) redact clinical PII entity types including Aadhaar, PAN, UPI IDs, and medical record numbers before any AI stage runs." },
  { icon: "🌐", title: "India Ready", desc: "Regional language support for Hindi and Telugu via Sarvam AI translation, with multilingual PII models trained specifically on Indian data." },
  { icon: "⚡", title: "Non-Blocking Pipeline", desc: "FastAPI responds in milliseconds. All heavy NLP runs asynchronously inside Celery workers backed by Upstash Redis in the cloud." },
  { icon: "📊", title: "Statistical Signals", desc: "PRR, ROR, and Chi-square statistics rank every drug-symptom pair. Only spikes that cross clinical thresholds become actionable signals." },
  { icon: "🤖", title: "Forum Onboarding AI", desc: "Drop any medical forum URL into the system and the AI generates a custom scraper config on the fly using Firecrawl plus Groq." },
  { icon: "🔬", title: "Explainable Output", desc: "Every AE flag shows its full reasoning trace: which drug, which symptom, the sentiment score, negation check result, and confidence value." },
  { icon: "🏗️", title: "Modular by Design", desc: "Each source is a plugin. Adding a new platform means writing one crawler class. The NLP pipeline, DB, and dashboard wire up automatically." },
  { icon: "📈", title: "Relational Risk Mapping", desc: "Future-ready: Mapping drug-symptom co-occurrence clusters. Medicines linked to high symptom counts are automatically flagged for prioritized risk testing." },
];

const MOAT_POINTS = [
  { 
    title: "Air-Gapped PII Shield", 
    desc: "Mandatory on-CPU redaction using OpenMed-44M/82M weights. Clinical PII is scrubbed locally BEFORE ingestion, ensuring HIPAA/GDPR compliance by design, not policy." 
  },
  { 
    title: "Clinical Entity Fusion", 
    desc: "Beyond generic NER. We use PharmaDetect-149M and DiseaseDetect-184M Transformers to isolate drug-symptom relationships in messy, unstructured vernacular social data." 
  },
  { 
    title: "Autonomous Scraper Synthesis", 
    desc: "Powered by Nvidia Nemotron-3. Our agent analyzes any forum's DOM on-the-fly to synthesize a crawler configuration—eliminating manual coding for new sources." 
  },
  { 
    title: "Dynamic MCP Query Routing", 
    desc: "The interface layer utilizes Model Context Protocol (MCP) to dynamically route user intent to specialized crawlers, ensuring optimized source selection for every query." 
  },
  { 
    title: "Async Scalability Architecture", 
    desc: "A hybrid stack using FastAPI for low-latency reactive UX and Celery/Redis for heavy background NLP handling, providing industrial-grade throughput and resilience." 
  },
  { 
    title: "Deterministic Signal Integrity", 
    desc: "Moving beyond LLM 'vibes.' We calculate PRR (Proportional Reporting Ratio) and ROR—the gold standard clinical math used by the FDA—to prove statistical significance." 
  }
];

const PIPELINE_STEPS = [
  { num: "01", label: "Vernacular Translation", detail: "Sarvam AI and local weights map regional side-effect slang (Hindi/Telugu) to standardized English." },
  { num: "02", label: "Local PII Guard", detail: "OpenMed-44M/82M scrubs clinical PII and Indian IDs (Aadhaar/PAN) on-CPU before any network call." },
  { num: "03", label: "PharmaDetect NER", detail: "OpenMed-149M clinical Transformer maps drug brand names to standardized MedDRA codes." },
  { num: "04", label: "DiseaseDetect NER", detail: "OpenMed-184M extracts pathological symptoms and adverse reactions from unstructured text." },
  { num: "05", label: "Sentiment Scoring", detail: "Twitter-RoBERTa (58M tweets) filters for 'Negative Sentiment' as a pre-requisite for AE detection." },
  { num: "06", label: "medspaCy Negation", detail: "Clinical rule-engines catch phrases like 'no nausea' to eliminate false positive signals." },
  { num: "07", label: "AE Detection Agent", detail: "Fused logic: [Drug + Symptom + Negative Sentiment + Not Negated] → Flagged Adverse Event." },
  { num: "08", label: "PRR Statistical Signal", detail: "Gold-standard PV math (PRR ≥ 2, χ² ≥ 4) validates if a signal is statistically significant vs. noise." },
];

function GridBackground() {
  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 0, overflow: "hidden", pointerEvents: "none" }}>
      <div style={{
        position: "absolute", inset: 0,
        backgroundImage: `
          linear-gradient(rgba(139,92,246,0.07) 1px, transparent 1px),
          linear-gradient(90deg, rgba(139,92,246,0.07) 1px, transparent 1px)
        `,
        backgroundSize: "48px 48px"
      }} />
      <div style={{
        position: "absolute", inset: 0,
        background: "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(139,92,246,0.18) 0%, transparent 70%)"
      }} />
      <div style={{
        position: "absolute", bottom: 0, left: 0, right: 0,
        background: "radial-gradient(ellipse 70% 40% at 50% 100%, rgba(79,70,229,0.12) 0%, transparent 70%)"
      }} />
    </div>
  );
}

function useInView(ref: React.RefObject<Element | null>) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true); }, { threshold: 0.15 });
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, [ref]);
  return visible;
}

function FadeIn({ children, delay = 0 }: { children: React.ReactNode; delay?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const visible = useInView(ref as React.RefObject<Element>);
  return (
    <div ref={ref} style={{
      opacity: visible ? 1 : 0,
      transform: visible ? "translateY(0)" : "translateY(28px)",
      transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`
    }}>
      {children}
    </div>
  );
}

function GlassCard({ children, style = {}, onClick, onMouseEnter, onMouseLeave }: {
  children: React.ReactNode;
  style?: React.CSSProperties;
  onClick?: () => void;
  onMouseEnter?: (e: React.MouseEvent<HTMLDivElement>) => void;
  onMouseLeave?: (e: React.MouseEvent<HTMLDivElement>) => void;
}) {
  return (
    <div onClick={onClick} onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave} style={{
      background: "rgba(255,255,255,0.035)",
      border: "1px solid rgba(255,255,255,0.09)",
      borderRadius: "16px",
      backdropFilter: "blur(12px)",
      ...style
    }}>
      {children}
    </div>
  );
}

export function LandingPage() {
  const [activeImg, setActiveImg] = useState<null | typeof ARTIFACTS[0]>(null);

  return (
    <div style={{ minHeight: "100vh", background: "#07070f", color: "#fff", fontFamily: "'Inter', 'Segoe UI', sans-serif", position: "relative", overflowX: "hidden" }}>
      <GridBackground />

      {/* Nav */}
      <nav style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 100, padding: "16px 40px", display: "flex", alignItems: "center", justifyContent: "space-between", background: "rgba(7,7,15,0.8)", backdropFilter: "blur(16px)", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #7c3aed, #4f46e5)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16 }}>⬡</div>
          <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: "-0.02em" }}>AlgoPharma</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <a href="https://github.com/Ankur2606/Algo-Pharma" target="_blank" rel="noreferrer" style={{ padding: "8px 18px", borderRadius: 8, border: "1px solid rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.7)", textDecoration: "none", fontSize: 13, fontWeight: 500, transition: "all 0.2s" }}>GitHub</a>
          <Link to="/login" style={{ padding: "8px 18px", borderRadius: 8, background: "linear-gradient(135deg, #7c3aed, #4f46e5)", color: "#fff", textDecoration: "none", fontSize: 13, fontWeight: 600 }}>Try Live Demo →</Link>
        </div>
      </nav>

      <div style={{ position: "relative", zIndex: 1, paddingTop: 100 }}>

        {/* Hero */}
        <section style={{ textAlign: "center", padding: "80px 24px 64px" }}>
          <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 16px", borderRadius: 999, border: "1px solid rgba(139,92,246,0.3)", background: "rgba(139,92,246,0.1)", marginBottom: 32, fontSize: 13, color: "rgba(167,139,250,1)" }}>
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#a78bfa", display: "inline-block" }} />
            AI for Bharat Hackathon 2026 · Theme 6: Real-Time Social Listening
          </div>
          <h1 style={{ fontSize: "clamp(40px, 6vw, 76px)", fontWeight: 800, lineHeight: 1.08, letterSpacing: "-0.04em", marginBottom: 24, maxWidth: 900, margin: "0 auto 24px" }}>
            Real-Time Pharmacovigilance{" "}
            <span style={{ background: "linear-gradient(135deg, #a78bfa, #818cf8, #60a5fa)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
              Powered by AI
            </span>
          </h1>
          <p style={{ fontSize: "clamp(16px, 2vw, 20px)", color: "rgba(255,255,255,0.52)", maxWidth: 680, margin: "0 auto 40px", lineHeight: 1.7 }}>
            AlgoPharma turns social media chatter into explainable drug safety signals. Chat with an AI agent, watch it crawl Reddit and Twitter, and see statistically ranked adverse event alerts appear on your dashboard in real time.
          </p>
          <div style={{ display: "flex", gap: 12, justifyContent: "center", flexWrap: "wrap" }}>
            <Link to="/login" style={{ padding: "14px 32px", borderRadius: 10, background: "linear-gradient(135deg, #7c3aed, #4f46e5)", color: "#fff", textDecoration: "none", fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em", boxShadow: "0 0 40px rgba(124,58,237,0.4)" }}>
              Launch Live App →
            </Link>
            <a href="https://github.com/Ankur2606/Algo-Pharma" target="_blank" rel="noreferrer" style={{ padding: "14px 32px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.12)", color: "rgba(255,255,255,0.8)", textDecoration: "none", fontSize: 15, fontWeight: 600 }}>
              View on GitHub
            </a>
          </div>

          {/* Stat row */}
          <div style={{ display: "flex", gap: 16, justifyContent: "center", marginTop: 56, flexWrap: "wrap" }}>
            {[
              { val: "8 Stage", label: "NLP Pipeline" },
              { val: "55+", label: "PII Entity Types" },
              { val: "3 Sources", label: "Reddit, Twitter, Forums" },
              { val: "PRR + ROR", label: "Signal Statistics" },
            ].map((s) => (
              <GlassCard key={s.label} style={{ padding: "20px 28px", textAlign: "center", minWidth: 130 }}>
                <p style={{ fontSize: 22, fontWeight: 700, color: "#a78bfa", marginBottom: 4 }}>{s.val}</p>
                <p style={{ fontSize: 12, color: "rgba(255,255,255,0.4)" }}>{s.label}</p>
              </GlassCard>
            ))}
          </div>
        </section>

        {/* Feature Flash Cards */}
        <section style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 24px 80px" }}>
          <FadeIn>
            <h2 style={{ textAlign: "center", fontSize: "clamp(24px, 3vw, 38px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 12 }}>Everything built from scratch</h2>
            <p style={{ textAlign: "center", color: "rgba(255,255,255,0.4)", marginBottom: 48, fontSize: 16 }}>No off-the-shelf safety platforms. Every layer engineered for this problem.</p>
          </FadeIn>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 16 }}>
            {FEATURES.map((f, i) => (
              <FadeIn key={f.title} delay={i * 60}>
                <GlassCard style={{ padding: "24px", height: "100%", transition: "border-color 0.2s", cursor: "default" }}>
                  <div style={{ fontSize: 28, marginBottom: 14 }}>{f.icon}</div>
                  <p style={{ fontWeight: 700, fontSize: 15, marginBottom: 10, letterSpacing: "-0.01em" }}>{f.title}</p>
                  <p style={{ fontSize: 13, color: "rgba(255,255,255,0.45)", lineHeight: 1.65 }}>{f.desc}</p>
                </GlassCard>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* The Moat Section */}
        <section style={{ maxWidth: 1200, margin: "0 auto", padding: "80px 24px", background: "#000", borderRadius: 32, border: "1px solid rgba(255,255,255,0.05)", marginBottom: 80 }}>
          <FadeIn>
            <div style={{ marginBottom: 48 }}>
               <span style={{ fontSize: 11, fontWeight: 700, color: "#fff", background: "#2563eb", padding: "4px 12px", borderRadius: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Competitive Advantage</span>
               <h2 style={{ fontSize: "clamp(30px, 5vw, 54px)", fontWeight: 700, letterSpacing: "-0.03em", marginTop: 24, marginBottom: 20 }}>
                 The <span style={{ color: "#fff", textDecoration: "underline", textDecorationColor: "rgba(255,255,255,0.2)" }}>AlgoPharma Moat</span>: Why Competitors Cannot Easily Replicate This
               </h2>
               <p style={{ fontSize: 18, color: "rgba(255,255,255,0.6)", maxWidth: 900, lineHeight: 1.6 }}>
                 AlgoPharma combines privacy-first architecture, agentic scalability, regional language dominance, and statistically rigorous signal detection into a single, defensible pharmacovigilance platform that no generic tool can match.
               </p>
            </div>
          </FadeIn>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 40 }}>
            {MOAT_POINTS.map((point, i) => (
              <FadeIn key={point.title} delay={i * 100}>
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <h3 style={{ fontSize: 20, fontWeight: 700, color: "#fff" }}>{point.title}</h3>
                  <p style={{ fontSize: 14, color: "rgba(255,255,255,0.5)", lineHeight: 1.7 }}>{point.desc}</p>
                </div>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* 8-Stage Pipeline */}
        <section style={{ maxWidth: 1100, margin: "0 auto", padding: "0 24px 80px" }}>
          <FadeIn>
            <h2 style={{ textAlign: "center", fontSize: "clamp(24px, 3vw, 38px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 12 }}>The 8-Stage NLP Funnel</h2>
            <p style={{ textAlign: "center", color: "rgba(255,255,255,0.4)", marginBottom: 48, fontSize: 16 }}>Every post travels through this pipeline before it can become a signal.</p>
          </FadeIn>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 14 }}>
            {PIPELINE_STEPS.map((s, i) => (
              <FadeIn key={s.num} delay={i * 55}>
                <GlassCard style={{ padding: "20px 22px", display: "flex", gap: 16, alignItems: "flex-start" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: "#7c3aed", background: "rgba(124,58,237,0.12)", borderRadius: 6, padding: "3px 8px", whiteSpace: "nowrap", marginTop: 2 }}>{s.num}</span>
                  <div>
                    <p style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{s.label}</p>
                    <p style={{ fontSize: 12, color: "rgba(255,255,255,0.42)", lineHeight: 1.6 }}>{s.detail}</p>
                  </div>
                </GlassCard>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* Architecture Diagrams Gallery */}
        <section style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px 80px" }}>
          <FadeIn>
            <h2 style={{ textAlign: "center", fontSize: "clamp(24px, 3vw, 38px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 12 }}>Architecture Deep Dive</h2>
            <p style={{ textAlign: "center", color: "rgba(255,255,255,0.4)", marginBottom: 48, fontSize: 16 }}>Click any diagram for a full view and description.</p>
          </FadeIn>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 18 }}>
            {ARTIFACTS.map((art, i) => (
              <FadeIn key={art.file} delay={i * 70}>
                <button
                  onClick={() => setActiveImg(art)}
                  style={{ all: "unset", display: "block", width: "100%", cursor: "pointer" }}
                >
                  <GlassCard style={{
                    overflow: "hidden",
                    transition: "transform 0.25s, border-color 0.25s",
                  }}
                    onMouseEnter={(e: any) => (e.currentTarget.style.transform = "translateY(-4px)")}
                    onMouseLeave={(e: any) => (e.currentTarget.style.transform = "translateY(0)")}
                  >
                    <div style={{ aspectRatio: "16/10", overflow: "hidden", background: "#0c0c1a" }}>
                      <img
                        src={art.file}
                        alt={art.title}
                        style={{ width: "100%", height: "100%", objectFit: "cover", display: "block", transition: "transform 0.4s", pointerEvents: "none" }}
                      />
                    </div>
                    <div style={{ padding: "16px 18px" }}>
                      <p style={{ fontWeight: 600, fontSize: 14, marginBottom: 6 }}>{art.title}</p>
                      <p style={{ fontSize: 12, color: "rgba(255,255,255,0.42)", lineHeight: 1.6 }}>{art.desc}</p>
                    </div>
                  </GlassCard>
                </button>
              </FadeIn>
            ))}
          </div>
        </section>

        {/* Team + CTA */}
        <section style={{ textAlign: "center", padding: "40px 24px 120px" }}>
          <FadeIn>
            <GlassCard style={{ maxWidth: 700, margin: "0 auto", padding: "48px 40px" }}>
              <div style={{ display: "inline-flex", gap: 8, marginBottom: 24 }}>
                {["AP", "AS", "AM"].map(i => (
                  <div key={i} style={{ width: 44, height: 44, borderRadius: "50%", background: "linear-gradient(135deg, #7c3aed, #4f46e5)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 13 }}>{i}</div>
                ))}
              </div>
              <p style={{ fontSize: 12, color: "rgba(255,255,255,0.35)", marginBottom: 6, letterSpacing: "0.08em", textTransform: "uppercase" }}>Algo Pharmacists · Team of 3</p>
              <h3 style={{ fontSize: "clamp(22px, 3vw, 32px)", fontWeight: 700, letterSpacing: "-0.03em", marginBottom: 14 }}>
                Because side effects shouldn't be a social experiment.
              </h3>
              <p style={{ fontSize: 15, color: "rgba(255,255,255,0.48)", lineHeight: 1.7, marginBottom: 32 }}>
                Built for the AI for Bharat Hackathon, Theme 6. We touched every layer — from Aadhaar-aware PII redaction to PRR signal statistics — with India's healthcare reality in mind.
              </p>
              <Link to="/login" style={{ display: "inline-block", padding: "14px 36px", borderRadius: 10, background: "linear-gradient(135deg, #7c3aed, #4f46e5)", color: "#fff", textDecoration: "none", fontSize: 15, fontWeight: 700, boxShadow: "0 0 48px rgba(124,58,237,0.45)" }}>
                Open AlgoPharma on Hugging Face →
              </Link>
            </GlassCard>
          </FadeIn>
        </section>
      </div>

      {/* Lightbox */}
      {activeImg && (
        <div
          onClick={() => setActiveImg(null)}
          style={{ position: "fixed", inset: 0, zIndex: 9999, background: "rgba(0,0,0,0.88)", display: "flex", alignItems: "center", justifyContent: "center", padding: 24, backdropFilter: "blur(8px)", cursor: "zoom-out" }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{ maxWidth: 1000, width: "100%", background: "#0c0c1a", borderRadius: 20, border: "1px solid rgba(255,255,255,0.1)", overflow: "hidden", cursor: "default", maxHeight: "90vh", display: "flex", flexDirection: "column" }}
          >
            <div style={{ overflow: "auto", flex: 1 }}>
              <img src={activeImg.file} alt={activeImg.title} style={{ width: "100%", display: "block" }} />
            </div>
            <div style={{ padding: "18px 28px", display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255,255,255,0.07)", flexShrink: 0 }}>
              <div>
                <p style={{ fontWeight: 700, fontSize: 16, marginBottom: 6 }}>{activeImg.title}</p>
                <p style={{ fontSize: 13, color: "rgba(255,255,255,0.48)", maxWidth: 700 }}>{activeImg.desc}</p>
              </div>
              <button onClick={() => setActiveImg(null)} style={{ background: "rgba(255,255,255,0.08)", border: "1px solid rgba(255,255,255,0.12)", color: "#fff", padding: "8px 20px", borderRadius: 8, cursor: "pointer", fontSize: 13, fontWeight: 500, whiteSpace: "nowrap", marginLeft: 24 }}>✕ Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
