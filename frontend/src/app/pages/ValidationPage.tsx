import { useMemo } from "react";
import { useLocation, useNavigate } from "react-router";
import { motion } from "motion/react";
import {
  ArrowLeft, MessageSquare, Twitter, Globe, ShieldCheck, AlertTriangle,
  XCircle, ThumbsUp, ThumbsDown, Minus, Clock, ExternalLink, Sparkles,
} from "lucide-react";
import { GlassCard, GlassInner, PageBackground } from "../components/GlassCard";

interface PVRequest { medicine: string | null; symptom: string | null; source: string | null }

// ── Mock thread data — in production this comes from FastAPI synthesis ──────
function buildMockThread(req: PVRequest) {
  const med = req.medicine || "the medication";
  const sym = (req.symptom || "the side effect").toLowerCase();
  const src = (req.source || "Reddit").toLowerCase();

  return {
    platform: src.includes("twitter") ? "Twitter" : src.includes("forum") ? "MedForum" : "Reddit",
    handle: src.includes("twitter") ? "@health_diaries_22" : src.includes("forum") ? "u/clinical_curious" : "u/quietstorm_42",
    subreddit: src.includes("twitter") ? null : src.includes("forum") ? "MedForum › Adverse Reactions" : "r/AskDocs",
    timeAgo: "4 hours ago",
    body: [
      { type: "text" as const, value: "Has anyone else had this happen — started taking " },
      { type: "med" as const, value: med },
      { type: "text" as const, value: " about a week ago and now I'm constantly dealing with " },
      { type: "sym" as const, value: sym },
      { type: "text" as const, value: ". Doctor said to monitor it but it's getting worse, not better. Never had this issue before. Is this normal or should I switch?" },
    ],
    upvotes: 142,
    replyCount: 23,
    confidence: "High" as "High" | "Medium" | "Low",
    threadScore: 0.82,
    corroborating: 3,
    contradicting: 1,
    neutral: 2,
    replies: [
      {
        id: "r1",
        stance: "corroborating" as const,
        author: src.includes("twitter") ? "@nina_writes" : "u/morning_chemist",
        timeAgo: "2 hours ago",
        text: `Same here — was on ${med} for 10 days and the ${sym} was unbearable. Stopped after talking to my pharmacist and it cleared in 48 hours.`,
      },
      {
        id: "r2",
        stance: "corroborating" as const,
        author: src.includes("twitter") ? "@dr_aisha_p" : "u/pv_nurse",
        timeAgo: "3 hours ago",
        text: `This is a documented ADR for ${med}. Frequency is listed as "uncommon" in the SmPC but we've seen a cluster this quarter. Please report to your country's PV authority.`,
      },
      {
        id: "r3",
        stance: "contradicting" as const,
        author: src.includes("twitter") ? "@meds_made_easy" : "u/skeptic_md",
        timeAgo: "5 hours ago",
        text: `${sym} is more likely related to dehydration or the underlying condition than ${med} itself. Don't jump to conclusions without bloodwork.`,
      },
    ],
  };
}

const PlatformIcon = ({ platform }: { platform: string }) => {
  const Icon = platform === "Twitter" ? Twitter : platform === "MedForum" ? Globe : MessageSquare;
  const color = platform === "Twitter" ? "#1da1f2" : platform === "MedForum" ? "#7ec8e3" : "#ff4500";
  return (
    <div style={{
      width: 32, height: 32, borderRadius: 8,
      display: "flex", alignItems: "center", justifyContent: "center",
      background: `${color}1f`, border: `1px solid ${color}40`,
    }}>
      <Icon className="w-4 h-4" style={{ color }} />
    </div>
  );
};

const ConfidenceBadge = ({ level, score }: { level: "High" | "Medium" | "Low"; score: number }) => {
  const cfg = {
    High: { color: "#22c55e", bg: "rgba(34,197,94,0.14)", border: "rgba(34,197,94,0.4)", Icon: ShieldCheck },
    Medium: { color: "#f59e0b", bg: "rgba(245,158,11,0.14)", border: "rgba(245,158,11,0.4)", Icon: AlertTriangle },
    Low: { color: "#ef4444", bg: "rgba(239,68,68,0.14)", border: "rgba(239,68,68,0.4)", Icon: XCircle },
  }[level];
  const Icon = cfg.Icon;
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 8,
      padding: "8px 14px", borderRadius: 999,
      background: cfg.bg,
      border: `1px solid ${cfg.border}`,
      borderTop: `1px solid ${cfg.color}66`,
      backdropFilter: "blur(10px)",
    }}>
      <Icon className="w-4 h-4" style={{ color: cfg.color }} />
      <span style={{ fontSize: 12, fontWeight: 700, color: cfg.color, letterSpacing: "0.04em" }}>
        {level.toUpperCase()} CONFIDENCE
      </span>
      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.55)", fontVariantNumeric: "tabular-nums" }}>
        {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
};

const StanceIcon = ({ stance }: { stance: "corroborating" | "contradicting" | "neutral" }) => {
  const cfg = {
    corroborating: { Icon: ThumbsUp, color: "#22c55e" },
    contradicting: { Icon: ThumbsDown, color: "#ef4444" },
    neutral: { Icon: Minus, color: "rgba(200,225,245,0.5)" },
  }[stance];
  const Icon = cfg.Icon;
  return <Icon className="w-3.5 h-3.5 shrink-0" style={{ color: cfg.color }} />;
};

export function ValidationPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const req = (location.state as PVRequest | null) ?? { medicine: "Ibuprofen", symptom: "GI Bleeding", source: "Reddit" };
  const thread = useMemo(() => buildMockThread(req), [req]);

  return (
    <PageBackground>
      {/* Header */}
      <header
        className="px-4 sm:px-6"
        style={{
          position: "sticky", top: 0, zIndex: 30,
          display: "flex", alignItems: "center", height: 52,
          background: "rgba(6,14,26,0.72)",
          backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
          borderBottom: "1px solid rgba(120,200,240,0.10)",
          borderTop: "1px solid rgba(255,255,255,0.06)",
          gap: 12,
        }}
      >
        <button
          onClick={() => navigate("/chat")}
          style={{
            display: "flex", alignItems: "center", gap: 6,
            padding: "6px 10px", borderRadius: 8,
            fontSize: 12, color: "rgba(200,225,245,0.7)",
            background: "rgba(15,40,75,0.4)",
            border: "1px solid rgba(120,200,240,0.14)",
            cursor: "pointer", flexShrink: 0,
          }}
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Back to chat</span>
        </button>
        <span
          className="truncate"
          style={{
            fontSize: 13, fontWeight: 700, letterSpacing: "-0.01em",
            background: "linear-gradient(110deg,#fff 40%,#7ec8e3 100%)",
            WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
            minWidth: 0,
          }}
        >
          <span className="hidden sm:inline">Thread Context & Validation</span>
          <span className="sm:hidden">Validation</span>
        </span>
        <div className="ml-auto hidden md:flex items-center gap-2 shrink-0" style={{ fontSize: 11, color: "rgba(200,225,245,0.45)" }}>
          <Clock className="w-3 h-3" />
          Synthesized just now
        </div>
      </header>

      {/* Content */}
      <main
        className="px-3 sm:px-5 pt-5 sm:pt-8 pb-12 sm:pb-16"
        style={{ maxWidth: 880, margin: "0 auto", display: "flex", flexDirection: "column", gap: 14 }}
      >

        {/* Extracted summary strip */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
          <GlassCard style={{ padding: "16px 20px" }}>
            <div className="flex items-center gap-3 flex-wrap">
              <Sparkles className="w-4 h-4" style={{ color: "#7ec8e3" }} />
              <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: "0.06em", color: "rgba(200,225,245,0.55)" }}>EXTRACTED</span>
              <Pill label={`Medicine · ${req.medicine}`} tone="med" />
              <Pill label={`Symptom · ${req.symptom}`} tone="sym" />
              <Pill label={`Source · ${req.source}`} tone="src" />
            </div>
          </GlassCard>
        </motion.div>

        {/* SOURCE POST SNIPPET */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.05 }}>
          <GlassCard style={{ padding: 0, overflow: "hidden" }}>
            <div
              className="px-4 sm:px-5"
              style={{
                display: "flex", alignItems: "center", gap: 10,
                paddingTop: 12, paddingBottom: 12,
                borderBottom: "1px solid rgba(120,200,240,0.08)",
              }}
            >
              <PlatformIcon platform={thread.platform} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="flex items-center gap-1.5 sm:gap-2 flex-wrap">
                  <span className="truncate" style={{ fontSize: 13, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>{thread.handle}</span>
                  {thread.subreddit && (
                    <span className="hidden sm:inline" style={{ fontSize: 11, color: "rgba(200,225,245,0.5)" }}>· {thread.subreddit}</span>
                  )}
                  <span style={{ fontSize: 11, color: "rgba(200,225,245,0.4)" }}>· {thread.timeAgo}</span>
                </div>
                <span style={{ fontSize: 10, color: "rgba(200,225,245,0.35)" }}>
                  ↑ {thread.upvotes} · 💬 {thread.replyCount} replies
                </span>
              </div>
              <button
                className="shrink-0"
                style={{
                  display: "flex", alignItems: "center", gap: 5,
                  padding: "6px 10px", borderRadius: 8,
                  fontSize: 11, color: "rgba(126,200,227,0.85)",
                  background: "rgba(20,55,100,0.4)",
                  border: "1px solid rgba(120,200,240,0.18)",
                  cursor: "pointer",
                }}
              >
                <ExternalLink className="w-3 h-3" />
                <span className="hidden sm:inline">Open original</span>
              </button>
            </div>

            <div className="px-4 sm:px-6 py-4 sm:py-5">
              <p style={{ fontSize: 14.5, color: "rgba(230,242,255,0.86)", lineHeight: 1.7 }}>
                {thread.body.map((seg, i) => {
                  if (seg.type === "text") return <span key={i}>{seg.value}</span>;
                  return <Pill key={i} label={seg.value} tone={seg.type === "med" ? "med" : "sym"} inline />;
                })}
              </p>
            </div>
          </GlassCard>
        </motion.div>

        {/* THREAD CORROBORATION */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.12 }}>
          <GlassCard style={{ padding: 0, overflow: "hidden" }}>
            <div
              className="px-4 sm:px-6 py-4"
              style={{
                display: "flex", alignItems: "stretch", gap: 14, flexWrap: "wrap",
                borderBottom: "1px solid rgba(120,200,240,0.08)",
              }}
            >
              <div>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", color: "rgba(200,225,245,0.45)", marginBottom: 6 }}>
                  THREAD SCORE
                </div>
                <ConfidenceBadge level={thread.confidence} score={thread.threadScore} />
              </div>
              <div style={{ flex: 1, minWidth: 240 }}>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: "0.08em", color: "rgba(200,225,245,0.45)", marginBottom: 8 }}>
                  REPLY SENTIMENT
                </div>
                <SentimentBar c={thread.corroborating} d={thread.contradicting} n={thread.neutral} />
                <div style={{ display: "flex", gap: 14, marginTop: 8, fontSize: 11, color: "rgba(200,225,245,0.7)" }}>
                  <span style={{ display: "flex", alignItems: "center", gap: 5 }}><span style={{ width: 8, height: 8, borderRadius: 2, background: "#22c55e" }} />{thread.corroborating} corroborating</span>
                  <span style={{ display: "flex", alignItems: "center", gap: 5 }}><span style={{ width: 8, height: 8, borderRadius: 2, background: "#ef4444" }} />{thread.contradicting} contradicting</span>
                  <span style={{ display: "flex", alignItems: "center", gap: 5 }}><span style={{ width: 8, height: 8, borderRadius: 2, background: "rgba(200,225,245,0.5)" }} />{thread.neutral} neutral</span>
                </div>
              </div>
            </div>

            {/* Reply mini-feed */}
            <div className="px-4 sm:px-6 pt-3 pb-4" style={{ maxHeight: 360, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
              {thread.replies.map((reply, i) => (
                <motion.div
                  key={reply.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.35, delay: 0.18 + i * 0.06 }}
                >
                  <GlassInner style={{ padding: "12px 14px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                      <StanceIcon stance={reply.stance} />
                      <span style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.78)" }}>{reply.author}</span>
                      <span style={{ fontSize: 10, color: "rgba(200,225,245,0.4)" }}>· {reply.timeAgo}</span>
                      <span style={{
                        marginLeft: "auto", fontSize: 9, fontWeight: 700, letterSpacing: "0.06em",
                        padding: "2px 7px", borderRadius: 4,
                        color: reply.stance === "corroborating" ? "#22c55e" : reply.stance === "contradicting" ? "#ef4444" : "rgba(200,225,245,0.6)",
                        background: reply.stance === "corroborating" ? "rgba(34,197,94,0.12)" : reply.stance === "contradicting" ? "rgba(239,68,68,0.12)" : "rgba(200,225,245,0.06)",
                      }}>
                        {reply.stance.toUpperCase()}
                      </span>
                    </div>
                    <p style={{ fontSize: 13, color: "rgba(220,235,255,0.78)", lineHeight: 1.6 }}>{reply.text}</p>
                  </GlassInner>
                </motion.div>
              ))}
            </div>
          </GlassCard>
        </motion.div>

        {/* TRIAGE ACTION BAR */}
        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, delay: 0.2 }}>
          <GlassCard style={{ padding: 0 }}>
            <div className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center gap-3 md:gap-4">
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: "rgba(255,255,255,0.85)" }}>Triage this signal</div>
                <div style={{ fontSize: 11, color: "rgba(200,225,245,0.5)", marginTop: 2 }}>
                  Action will be logged to the audit trail and synced to VigiFlow.
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-2.5 w-full md:w-auto">
                <ActionButton tone="primary" Icon={ShieldCheck} label="Validate & Save Signal" onClick={() => alert("Signal validated and saved")} />
                <ActionButton tone="warn" Icon={AlertTriangle} label="Escalate for Review" onClick={() => alert("Escalated for clinical review")} />
                <ActionButton tone="ghost" Icon={XCircle} label="Mark False Positive" onClick={() => alert("Marked as false positive")} />
              </div>
            </div>
          </GlassCard>
        </motion.div>
      </main>
    </PageBackground>
  );
}

// ── Inline pieces ──────────────────────────────────────────────────────────

function Pill({ label, tone, inline }: { label: string; tone: "med" | "sym" | "src"; inline?: boolean }) {
  const palette = {
    med: { color: "#7ec8e3", bg: "rgba(40,130,210,0.18)", border: "rgba(126,200,227,0.45)" },
    sym: { color: "#fbbf24", bg: "rgba(245,158,11,0.16)", border: "rgba(245,158,11,0.45)" },
    src: { color: "#a5b4fc", bg: "rgba(120,90,220,0.18)", border: "rgba(165,180,252,0.4)" },
  }[tone];
  return (
    <span style={{
      display: "inline-flex", alignItems: "center",
      padding: inline ? "1px 8px" : "5px 11px",
      margin: inline ? "0 2px" : 0,
      borderRadius: inline ? 6 : 999,
      fontSize: inline ? "0.95em" : 11,
      fontWeight: inline ? 600 : 500,
      color: palette.color,
      background: palette.bg,
      border: `1px solid ${palette.border}`,
      borderTop: `1px solid ${palette.color}66`,
      lineHeight: inline ? "inherit" : 1.4,
      whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

function SentimentBar({ c, d, n }: { c: number; d: number; n: number }) {
  const total = c + d + n || 1;
  return (
    <div style={{
      display: "flex", height: 8, borderRadius: 4, overflow: "hidden",
      background: "rgba(255,255,255,0.04)",
      border: "1px solid rgba(120,200,240,0.1)",
    }}>
      <motion.div initial={{ width: 0 }} animate={{ width: `${(c / total) * 100}%` }} transition={{ duration: 0.7, delay: 0.2 }} style={{ background: "linear-gradient(90deg,#22c55e,#16a34a)" }} />
      <motion.div initial={{ width: 0 }} animate={{ width: `${(d / total) * 100}%` }} transition={{ duration: 0.7, delay: 0.3 }} style={{ background: "linear-gradient(90deg,#ef4444,#dc2626)" }} />
      <motion.div initial={{ width: 0 }} animate={{ width: `${(n / total) * 100}%` }} transition={{ duration: 0.7, delay: 0.4 }} style={{ background: "rgba(200,225,245,0.4)" }} />
    </div>
  );
}

function ActionButton({ tone, Icon, label, onClick }: {
  tone: "primary" | "warn" | "ghost";
  Icon: React.ElementType; label: string; onClick: () => void;
}) {
  const palette = {
    primary: {
      color: "#fff",
      bg: "linear-gradient(135deg, rgba(34,197,94,0.85) 0%, rgba(22,163,74,0.85) 100%)",
      border: "rgba(34,197,94,0.5)",
      glow: "0 0 24px rgba(34,197,94,0.45)",
    },
    warn: {
      color: "#fff7e0",
      bg: "linear-gradient(135deg, rgba(245,158,11,0.7) 0%, rgba(217,119,6,0.7) 100%)",
      border: "rgba(245,158,11,0.5)",
      glow: "0 0 24px rgba(245,158,11,0.4)",
    },
    ghost: {
      color: "rgba(239,68,68,0.92)",
      bg: "rgba(239,68,68,0.08)",
      border: "rgba(239,68,68,0.3)",
      glow: "none",
    },
  }[tone];
  return (
    <motion.button
      whileHover={{ y: -2, boxShadow: palette.glow !== "none" ? palette.glow : "0 0 18px rgba(239,68,68,0.25)" }}
      whileTap={{ scale: 0.97 }}
      onClick={onClick}
      className="w-full sm:w-auto justify-center sm:justify-start"
      style={{
        display: "inline-flex", alignItems: "center", gap: 8,
        padding: "10px 16px", borderRadius: 10,
        fontSize: 12.5, fontWeight: 600, whiteSpace: "nowrap",
        color: palette.color,
        background: palette.bg,
        border: `1px solid ${palette.border}`,
        borderTop: `1px solid ${tone === "ghost" ? "rgba(239,68,68,0.4)" : "rgba(255,255,255,0.32)"}`,
        backdropFilter: "blur(10px)",
        boxShadow: tone !== "ghost" ? "inset 0 1px 0 rgba(255,255,255,0.18)" : "none",
        cursor: "pointer",
      }}
    >
      <Icon className="w-3.5 h-3.5" />
      {label}
    </motion.button>
  );
}
