import { useParams, useNavigate } from "react-router";
import { Header } from "../components/layout/Header";
import { SeverityBadge } from "../components/shared/SeverityBadge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { signals, posts } from "../data/mockData";
import {
  CheckCircle,
  Download,
  ExternalLink,
  MessageSquare,
  ArrowLeft,
  Check,
  X,
  AlertCircle,
  MinusCircle,
  ThumbsUp,
  ThumbsDown,
  Minus,
} from "lucide-react";
import { useState } from "react";

const gates = [
  { label: "Gate 1: Drug entity found", pass: true, detail: "Found: 'ibuprofen' (conf: 98%)" },
  { label: "Gate 2: Symptom/ADR found", pass: true, detail: "Found: 'gastrointestinal bleeding' (conf: 94%)" },
  { label: "Gate 3: Negative sentiment", pass: true, detail: "Sentiment: NEGATIVE (score: -0.87)" },
  { label: "Gate 4: No full negation", pass: true, detail: "No full negation detected" },
];

function SentimentIcon({ sentiment }: { sentiment: "NEGATIVE" | "NEUTRAL" | "POSITIVE" }) {
  if (sentiment === "NEGATIVE")
    return <ThumbsDown className="w-3.5 h-3.5 text-red-400" />;
  if (sentiment === "POSITIVE")
    return <ThumbsUp className="w-3.5 h-3.5 text-green-400" />;
  return <Minus className="w-3.5 h-3.5 text-white/40" />;
}

function SentimentBadge({ sentiment }: { sentiment: "NEGATIVE" | "NEUTRAL" | "POSITIVE" }) {
  const config = {
    NEGATIVE: "bg-red-500/10 text-red-400 border-red-500/20",
    NEUTRAL: "bg-white/5 text-white/50 border-white/10",
    POSITIVE: "bg-green-500/10 text-green-400 border-green-500/20",
  };
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${config[sentiment]}`}
    >
      <SentimentIcon sentiment={sentiment} />
      {sentiment}
    </span>
  );
}

export function SignalDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [confirmed, setConfirmed] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);
  const [note, setNote] = useState("");

  const signal = signals.find((s) => s.id === id) ?? signals[0];
  const signalPosts = posts.filter((p) => p.signalId === signal.id).concat(posts).slice(0, 3);

  const strengthLabel =
    signal.prr >= 5 ? "STRONG" : signal.prr >= 2 ? "MODERATE" : "WEAK";
  const strengthColor =
    signal.prr >= 5
      ? "text-red-400 border-red-500/20 bg-red-500/10"
      : signal.prr >= 2
      ? "text-amber-400 border-amber-400/20 bg-amber-400/10"
      : "text-green-400 border-green-400/20 bg-green-400/10";

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header
        title={`${signal.drug} → ${signal.symptom}`}
        subtitle={`Signal ID: ${signal.id} · ${signal.source}`}
        actions={
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-white/40 hover:text-white/70 transition-colors text-sm"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-4">
        {/* Header Section */}
        <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="flex flex-wrap items-start gap-4 justify-between">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-white" style={{ fontSize: "20px", fontWeight: 700 }}>
                  {signal.drug}
                </h2>
                <span className="text-white/30">→</span>
                <span className="text-white/70" style={{ fontSize: "18px" }}>
                  {signal.symptom}
                </span>
                <span
                  className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${strengthColor}`}
                >
                  {strengthLabel} SIGNAL
                </span>
                <SeverityBadge severity={signal.severity} />
                <StatusBadge status={signal.status} />
              </div>
              <div className="flex flex-wrap gap-4 mt-4">
                {[
                  { label: "PRR", value: signal.prr.toFixed(2), tooltip: "Proportional Reporting Ratio" },
                  { label: "ROR", value: signal.ror.toFixed(2), tooltip: "Reporting Odds Ratio" },
                  { label: "Chi²", value: signal.chi2.toFixed(1), tooltip: "Chi-squared statistic" },
                  { label: "Posts", value: signal.postCount.toLocaleString(), tooltip: "Total posts analyzed" },
                  { label: "Confidence", value: `${signal.confidence}%`, tooltip: "Model confidence" },
                ].map(({ label, value }) => (
                  <div key={label}>
                    <p className="text-white/30" style={{ fontSize: "11px" }}>{label}</p>
                    <p className="text-white/80 font-mono mt-0.5" style={{ fontSize: "15px", fontWeight: 600 }}>
                      {value}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => setConfirmed(true)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  confirmed
                    ? "bg-green-500/20 text-green-400 border border-green-500/30"
                    : "bg-indigo-600 hover:bg-indigo-500 text-white"
                }`}
              >
                <CheckCircle className="w-4 h-4" />
                {confirmed ? "Confirmed" : "Confirm Signal"}
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/[0.06] hover:bg-white/[0.10] text-white/70 border border-white/[0.08] transition-colors">
                <Download className="w-4 h-4" /> Export to VigiFlow
              </button>
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/[0.06] hover:bg-white/[0.10] text-white/70 border border-white/[0.08] transition-colors">
                <ExternalLink className="w-4 h-4" /> Source Posts
              </button>
              <button
                onClick={() => setNoteOpen(!noteOpen)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-white/[0.06] hover:bg-white/[0.10] text-white/70 border border-white/[0.08] transition-colors"
              >
                <MessageSquare className="w-4 h-4" /> Add Note
              </button>
            </div>
          </div>

          {noteOpen && (
            <div className="mt-4 pt-4 border-t border-white/[0.06]">
              <textarea
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Add internal analyst note..."
                rows={3}
                className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-4 py-3 text-white/70 text-sm placeholder:text-white/30 focus:outline-none focus:border-indigo-500/40 resize-none"
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => setNoteOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                >
                  Save Note
                </button>
                <button
                  onClick={() => setNoteOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-sm text-white/40 hover:text-white/60 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-4">
          {/* Explainability Panel */}
          <div className="lg:col-span-2 rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Explainability Trace
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              Why was this signal flagged?
            </p>

            <div className="space-y-3">
              {gates.map((gate, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div
                    className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                      gate.pass
                        ? "bg-green-500/20 border border-green-500/30"
                        : "bg-red-500/20 border border-red-500/30"
                    }`}
                  >
                    {gate.pass ? (
                      <Check className="w-3 h-3 text-green-400" />
                    ) : (
                      <X className="w-3 h-3 text-red-400" />
                    )}
                  </div>
                  <div>
                    <p
                      className={`${gate.pass ? "text-white/70" : "text-white/40"}`}
                      style={{ fontSize: "13px", fontWeight: 500 }}
                    >
                      {gate.label}
                    </p>
                    <p className="text-white/30 mt-0.5" style={{ fontSize: "11px" }}>
                      {gate.detail}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 pt-4 border-t border-white/[0.06]">
              <p className="text-white/30 mb-3" style={{ fontSize: "11px", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                Statistical Reasoning
              </p>
              <div className="space-y-2">
                {[
                  { label: "PRR > 5 threshold", pass: signal.prr >= 5 },
                  { label: "Chi² > 4 threshold", pass: signal.chi2 >= 4 },
                  { label: "Post count ≥ 50", pass: signal.postCount >= 50 },
                  { label: "Confidence ≥ 70%", pass: signal.confidence >= 70 },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-2">
                    {item.pass ? (
                      <CheckCircle className="w-3.5 h-3.5 text-green-400 shrink-0" />
                    ) : (
                      <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                    )}
                    <span
                      className={`${item.pass ? "text-white/60" : "text-white/30"}`}
                      style={{ fontSize: "12px" }}
                    >
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Post Feed */}
          <div className="lg:col-span-3 rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Post Feed
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              NLP-analyzed posts · PII redacted
            </p>
            <div className="space-y-4">
              {signalPosts.map((post) => (
                <div
                  key={post.id}
                  className="rounded-lg p-4"
                  style={{ background: "rgba(255,255,255,0.025)", border: "1px solid rgba(255,255,255,0.06)" }}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-white/30" style={{ fontSize: "11px" }}>
                        {post.platform}
                      </span>
                      <SentimentBadge sentiment={post.sentiment} />
                      <span className="text-white/20" style={{ fontSize: "11px" }}>
                        Conf: {post.confidence}%
                      </span>
                    </div>
                    <span className="text-white/20 shrink-0" style={{ fontSize: "11px" }}>
                      {post.replyCount} replies
                    </span>
                  </div>

                  <p className="leading-relaxed" style={{ fontSize: "13px" }}>
                    {post.highlightedText.segments.map((seg, i) => {
                      if (seg.type === "drug")
                        return (
                          <mark
                            key={i}
                            className="bg-blue-500/20 text-blue-300 px-0.5 rounded-sm"
                          >
                            {seg.text}
                          </mark>
                        );
                      if (seg.type === "symptom")
                        return (
                          <mark
                            key={i}
                            className="bg-red-500/20 text-red-300 px-0.5 rounded-sm"
                          >
                            {seg.text}
                          </mark>
                        );
                      if (seg.type === "redacted")
                        return (
                          <mark
                            key={i}
                            className="bg-white/10 text-white/30 px-0.5 rounded-sm font-mono"
                            style={{ fontSize: "11px" }}
                          >
                            {seg.text}
                          </mark>
                        );
                      return (
                        <span key={i} className="text-white/60">
                          {seg.text}
                        </span>
                      );
                    })}
                  </p>

                  {/* Corroboration */}
                  <div className="mt-3 flex items-center gap-3">
                    <span className="text-white/30" style={{ fontSize: "11px" }}>
                      Corroboration
                    </span>
                    <div className="flex-1 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          post.corroborationScore > 70
                            ? "bg-green-500"
                            : post.corroborationScore > 40
                            ? "bg-amber-400"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${post.corroborationScore}%` }}
                      />
                    </div>
                    <span
                      className={`font-mono ${
                        post.corroborationScore > 70
                          ? "text-green-400"
                          : post.corroborationScore > 40
                          ? "text-amber-400"
                          : "text-red-400"
                      }`}
                      style={{ fontSize: "12px" }}
                    >
                      {post.corroborationScore}%
                    </span>
                  </div>

                  {/* Reply breakdown */}
                  {post.replyCount > 4 && (
                    <div className="mt-3 flex items-center gap-3 flex-wrap">
                      {[
                        { icon: CheckCircle, label: "Corroborating", count: Math.floor(post.replyCount * 0.5), color: "text-green-400" },
                        { icon: AlertCircle, label: "Weak", count: Math.floor(post.replyCount * 0.2), color: "text-amber-400" },
                        { icon: X, label: "Contradicting", count: Math.floor(post.replyCount * 0.15), color: "text-red-400" },
                        { icon: MinusCircle, label: "Neutral", count: Math.floor(post.replyCount * 0.15), color: "text-white/30" },
                      ].map(({ icon: Icon, label, count, color }) => (
                        <div key={label} className={`flex items-center gap-1 ${color}`} style={{ fontSize: "11px" }}>
                          <Icon className="w-3 h-3" />
                          {count} {label}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex items-center gap-3 mt-3" style={{ fontSize: "12px" }}>
              <span className="w-2.5 h-2.5 rounded-sm bg-blue-500/30 inline-block" />
              <span className="text-white/30">= Drug entity</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-red-500/30 inline-block ml-2" />
              <span className="text-white/30">= Symptom/ADR</span>
              <span className="w-2.5 h-2.5 rounded-sm bg-white/10 inline-block ml-2" />
              <span className="text-white/30">= PII redacted</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}