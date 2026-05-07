import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  Globe,
  ShieldCheck,
  Tags,
  BrainCircuit,
  AlertTriangle,
  BarChart2,
  CheckCircle2,
} from "lucide-react";
import { PageBackground } from "../components/GlassCard";

// Pipeline step definitions — mirrors backend processing order
const PIPELINE_STEPS = [
  {
    id: "crawling",
    label: "Crawling sources",
    sub: "Scraping Reddit & Twitter threads",
    Icon: Globe,
    color: "#38bdf8",
    glow: "rgba(56,189,248,0.35)",
    durationMs: 2200,
  },
  {
    id: "pii",
    label: "PII Redaction",
    sub: "Anonymising user-identifiable information",
    Icon: ShieldCheck,
    color: "#818cf8",
    glow: "rgba(129,140,248,0.35)",
    durationMs: 1800,
  },
  {
    id: "ner",
    label: "Named Entity Recognition",
    sub: "Extracting drugs, symptoms, dosages",
    Icon: Tags,
    color: "#a78bfa",
    glow: "rgba(167,139,250,0.35)",
    durationMs: 2000,
  },
  {
    id: "nlp",
    label: "NLP Analysis",
    sub: "Sentiment scoring & context classification",
    Icon: BrainCircuit,
    color: "#f472b6",
    glow: "rgba(244,114,182,0.35)",
    durationMs: 2000,
  },
  {
    id: "ae",
    label: "Adverse Event Detection",
    sub: "Identifying potential drug reactions",
    Icon: AlertTriangle,
    color: "#fb923c",
    glow: "rgba(251,146,60,0.35)",
    durationMs: 1800,
  },
  {
    id: "signal",
    label: "Signal Detection",
    sub: "Computing PRR, ROR, χ² statistics",
    Icon: BarChart2,
    color: "#4ade80",
    glow: "rgba(74,222,128,0.35)",
    durationMs: 2200,
  },
] as const;

const TOTAL_MS = PIPELINE_STEPS.reduce((s, p) => s + p.durationMs, 0);

export function ProcessingPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("project_id");

  // Index of the step currently running (-1 = not started)
  const [activeStep, setActiveStep] = useState(0);
  const [completed, setCompleted] = useState<Set<number>>(new Set());
  const [done, setDone] = useState(false);

  useEffect(() => {
    let stepIndex = 0;
    let timeout: ReturnType<typeof setTimeout>;

    function advanceStep() {
      if (stepIndex >= PIPELINE_STEPS.length) {
        setDone(true);
        // Wait a beat so the user can see the last checkmark, then navigate
        timeout = setTimeout(() => {
          navigate(`/dashboard?project_id=${projectId ?? ""}`, { replace: true });
        }, 1200);
        return;
      }

      const step = PIPELINE_STEPS[stepIndex];
      setActiveStep(stepIndex);

      timeout = setTimeout(() => {
        setCompleted((prev) => new Set([...prev, stepIndex]));
        stepIndex++;
        // small gap between steps
        timeout = setTimeout(advanceStep, 280);
      }, step.durationMs);
    }

    advanceStep();
    return () => clearTimeout(timeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const progress = done
    ? 100
    : Math.round(
        (PIPELINE_STEPS.slice(0, activeStep).reduce((s, p) => s + p.durationMs, 0) /
          TOTAL_MS) *
          100
      );

  return (
    <PageBackground>
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px 16px",
        }}
      >
        {/* ── Title ── */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          style={{ textAlign: "center", marginBottom: 48 }}
        >
          {/* Orbital spinner */}
          <div
            style={{
              position: "relative",
              width: 80,
              height: 80,
              margin: "0 auto 24px",
            }}
          >
            {[0, 1, 2].map((i) => (
              <motion.div
                key={i}
                animate={{ rotate: 360 }}
                transition={{
                  duration: 3 + i * 0.7,
                  repeat: Infinity,
                  ease: "linear",
                }}
                style={{
                  position: "absolute",
                  inset: i * 10,
                  borderRadius: "50%",
                  border: "1px solid transparent",
                  borderTopColor: `rgba(129,140,248,${0.7 - i * 0.18})`,
                  borderRightColor: `rgba(56,189,248,${0.5 - i * 0.12})`,
                }}
              />
            ))}
            {/* Center dot */}
            <div
              style={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <motion.div
                animate={{ scale: [1, 1.25, 1] }}
                transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
                style={{
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: "#818cf8",
                  boxShadow: "0 0 14px rgba(129,140,248,0.8)",
                }}
              />
            </div>
          </div>

          <h1
            style={{
              fontSize: "clamp(20px, 3vw, 28px)",
              fontWeight: 800,
              letterSpacing: "-0.02em",
              background: "linear-gradient(110deg, #ffffff 30%, #818cf8 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              marginBottom: 8,
            }}
          >
            Running Analysis Pipeline
          </h1>
          <p
            style={{
              fontSize: "clamp(12px, 1.5vw, 14px)",
              color: "rgba(200,215,255,0.45)",
            }}
          >
            Project #{projectId ?? "–"} · Please wait while we process the data
          </p>
        </motion.div>

        {/* ── Pipeline steps ── */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
          style={{
            width: "100%",
            maxWidth: "min(520px, 92vw)",
            display: "flex",
            flexDirection: "column",
            gap: 10,
          }}
        >
          {PIPELINE_STEPS.map((step, idx) => {
            const isDone = completed.has(idx);
            const isActive = activeStep === idx && !isDone;
            const Icon = step.Icon;

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -14 }}
                animate={{ opacity: idx <= activeStep ? 1 : 0.32, x: 0 }}
                transition={{
                  duration: 0.4,
                  delay: 0.05 * idx,
                  ease: [0.22, 1, 0.36, 1],
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "clamp(12px, 1.5vw, 16px) clamp(14px, 2vw, 20px)",
                  borderRadius: 12,
                  position: "relative",
                  overflow: "hidden",
                  background: isActive
                    ? "rgba(20,20,36,0.7)"
                    : isDone
                    ? "rgba(14,14,22,0.5)"
                    : "rgba(10,10,18,0.35)",
                  border: isActive
                    ? `1px solid ${step.color}44`
                    : isDone
                    ? "1px solid rgba(74,222,128,0.15)"
                    : "1px solid rgba(255,255,255,0.05)",
                  borderTop: isActive
                    ? `1px solid ${step.color}66`
                    : isDone
                    ? "1px solid rgba(74,222,128,0.22)"
                    : "1px solid rgba(255,255,255,0.08)",
                  backdropFilter: "blur(10px)",
                  boxShadow: isActive ? `0 0 24px ${step.glow}` : "none",
                  transition: "border 0.3s ease, box-shadow 0.3s ease, background 0.3s ease",
                }}
              >
                {/* Subtle reflection */}
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: "inherit",
                    background:
                      "linear-gradient(135deg, rgba(255,255,255,0.045) 0%, transparent 45%)",
                    pointerEvents: "none",
                  }}
                />

                {/* Icon container */}
                <div
                  style={{
                    position: "relative",
                    width: 36,
                    height: 36,
                    borderRadius: 10,
                    flexShrink: 0,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: isDone
                      ? "rgba(74,222,128,0.12)"
                      : isActive
                      ? `${step.color}18`
                      : "rgba(255,255,255,0.04)",
                    border: isDone
                      ? "1px solid rgba(74,222,128,0.25)"
                      : isActive
                      ? `1px solid ${step.color}35`
                      : "1px solid rgba(255,255,255,0.07)",
                    transition: "all 0.35s ease",
                  }}
                >
                  <AnimatePresence mode="wait">
                    {isDone ? (
                      <motion.div
                        key="check"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                        transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
                      >
                        <CheckCircle2
                          className="w-4 h-4"
                          style={{ color: "#4ade80" }}
                        />
                      </motion.div>
                    ) : (
                      <motion.div
                        key="icon"
                        initial={{ scale: 0.8, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.8, opacity: 0 }}
                        transition={{ duration: 0.22 }}
                      >
                        <Icon
                          className="w-4 h-4"
                          style={{
                            color: isActive ? step.color : "rgba(255,255,255,0.28)",
                            transition: "color 0.3s ease",
                          }}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Text */}
                <div style={{ flex: 1, minWidth: 0, position: "relative" }}>
                  <p
                    style={{
                      fontSize: "clamp(12px, 1.4vw, 14px)",
                      fontWeight: 600,
                      color: isDone
                        ? "rgba(74,222,128,0.85)"
                        : isActive
                        ? "#fff"
                        : "rgba(255,255,255,0.38)",
                      transition: "color 0.3s ease",
                    }}
                  >
                    {step.label}
                  </p>
                  <p
                    style={{
                      fontSize: "clamp(10px, 1.2vw, 12px)",
                      color: isActive
                        ? "rgba(200,215,255,0.45)"
                        : "rgba(255,255,255,0.2)",
                      marginTop: 2,
                      transition: "color 0.3s ease",
                    }}
                  >
                    {step.sub}
                  </p>
                </div>

                {/* Active pulse bar on right */}
                {isActive && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    style={{
                      position: "relative",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      flexShrink: 0,
                    }}
                  >
                    {[0, 1, 2].map((i) => (
                      <motion.span
                        key={i}
                        animate={{ scaleY: [0.5, 1.4, 0.5] }}
                        transition={{
                          duration: 0.9,
                          delay: i * 0.18,
                          repeat: Infinity,
                          ease: "easeInOut",
                        }}
                        style={{
                          display: "block",
                          width: 3,
                          height: 14,
                          borderRadius: 2,
                          background: step.color,
                          opacity: 0.8,
                        }}
                      />
                    ))}
                  </motion.div>
                )}

                {/* Done checkmark badge */}
                {isDone && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    style={{
                      flexShrink: 0,
                      fontSize: 10,
                      fontWeight: 700,
                      color: "#4ade80",
                      background: "rgba(74,222,128,0.1)",
                      border: "1px solid rgba(74,222,128,0.2)",
                      borderRadius: 100,
                      padding: "2px 8px",
                    }}
                  >
                    Done
                  </motion.span>
                )}
              </motion.div>
            );
          })}
        </motion.div>

        {/* ── Progress bar ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          style={{
            marginTop: 32,
            width: "100%",
            maxWidth: "min(520px, 92vw)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              marginBottom: 8,
            }}
          >
            <p style={{ fontSize: 11, color: "rgba(200,215,255,0.35)" }}>
              Overall progress
            </p>
            <p
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "rgba(200,215,255,0.6)",
              }}
            >
              {progress}%
            </p>
          </div>
          <div
            style={{
              width: "100%",
              height: 4,
              borderRadius: 4,
              background: "rgba(255,255,255,0.06)",
              overflow: "hidden",
            }}
          >
            <motion.div
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.6, ease: "easeOut" }}
              style={{
                height: "100%",
                borderRadius: 4,
                background: "linear-gradient(90deg, #818cf8, #38bdf8)",
                boxShadow: "0 0 8px rgba(129,140,248,0.5)",
              }}
            />
          </div>
        </motion.div>
      </div>
    </PageBackground>
  );
}
