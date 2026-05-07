import { useState } from "react";
import { useNavigate } from "react-router";
import {
  Shield,
  Eye,
  EyeOff,
  Lock,
  Mail,
  ArrowRight,
  Activity,
  AlertTriangle,
  TrendingUp,
  FileText,
  ChevronRight,
} from "lucide-react";

// Mini dashboard preview data
const previewSignals = [
  { drug: "Sertraline", symptom: "Suicidal Ideation", prr: "9.1", sev: "RED", status: "IN_REVIEW" },
  { drug: "Ibuprofen", symptom: "GI Bleeding", prr: "7.2", sev: "RED", status: "NEW" },
  { drug: "Metformin", symptom: "Lactic Acidosis", prr: "6.8", sev: "RED", status: "IN_REVIEW" },
  { drug: "Atorvastatin", symptom: "Myopathy", prr: "3.4", sev: "AMBER", status: "IN_REVIEW" },
  { drug: "Amlodipine", symptom: "Peripheral Edema", prr: "2.9", sev: "AMBER", status: "CONFIRMED" },
];

function SevDot({ sev }: { sev: string }) {
  const c =
    sev === "RED" ? "bg-red-500" : sev === "AMBER" ? "bg-amber-400" : "bg-green-500";
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${c} mr-1.5`} />;
}

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("analyst@algopharma.in");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => navigate("/chat"), 900);
  };

  return (
    <div
      className="min-h-screen w-full overflow-x-hidden"
      style={{ background: "#050508" }}
    >
      {/* ── Grid background ── */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.022) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.022) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* ── Radial glow ── */}
      <div
        className="fixed pointer-events-none"
        style={{
          top: "0",
          left: "50%",
          transform: "translateX(-50%)",
          width: "800px",
          height: "500px",
          background:
            "radial-gradient(ellipse at center top, rgba(99,102,241,0.12) 0%, transparent 70%)",
        }}
      />

      {/* ══════════════════ NAV ══════════════════ */}
      <nav
        className="relative z-20 flex items-center justify-between px-8 md:px-12"
        style={{ height: "58px", borderBottom: "1px solid rgba(255,255,255,0.055)" }}
      >
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div
            className="flex items-center justify-center rounded-lg"
            style={{
              width: "30px",
              height: "30px",
              background: "rgba(99,102,241,0.18)",
              border: "1px solid rgba(99,102,241,0.3)",
            }}
          >
            <Shield className="w-4 h-4" style={{ color: "#818cf8" }} />
          </div>
          <span
            className="text-white/90 tracking-tight"
            style={{ fontSize: "14px", fontWeight: 600 }}
          >
            AlgoPharma
          </span>
          <span
            className="px-1.5 py-0.5 rounded"
            style={{
              fontSize: "10px",
              fontWeight: 600,
              background: "rgba(99,102,241,0.15)",
              color: "#818cf8",
              border: "1px solid rgba(99,102,241,0.25)",
            }}
          >
            PV
          </span>
        </div>

        {/* Center links */}
        <div className="hidden md:flex items-center gap-7">
          {["Dashboard", "Signals", "Analytics", "Documentation"].map((l) => (
            <button
              key={l}
              className="transition-colors"
              style={{ fontSize: "13px", color: "rgba(255,255,255,0.45)" }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLElement).style.color =
                  "rgba(255,255,255,0.80)")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLElement).style.color =
                  "rgba(255,255,255,0.45)")
              }
            >
              {l}
            </button>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 transition-colors"
          style={{
            fontSize: "13px",
            fontWeight: 500,
            padding: "7px 16px",
            borderRadius: "7px",
            border: "1px solid rgba(255,255,255,0.12)",
            color: "rgba(255,255,255,0.65)",
            background: "transparent",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.borderColor =
              "rgba(255,255,255,0.22)";
            (e.currentTarget as HTMLElement).style.color =
              "rgba(255,255,255,0.9)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.borderColor =
              "rgba(255,255,255,0.12)";
            (e.currentTarget as HTMLElement).style.color =
              "rgba(255,255,255,0.65)";
          }}
        >
          Sign in <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </nav>

      {/* ══════════════════ HERO ══════════════════ */}
      <div className="relative z-10 flex flex-col items-center text-center px-6 pt-20 pb-10">
        {/* Badge */}
        <div
          className="inline-flex items-center gap-2 mb-9"
          style={{
            padding: "6px 14px",
            borderRadius: "100px",
            border: "1px solid rgba(255,255,255,0.09)",
            background: "rgba(255,255,255,0.03)",
          }}
        >
          <span
            className="flex h-1.5 w-1.5 relative"
          >
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500" />
          </span>
          <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.45)", fontWeight: 500 }}>
            5 crawlers active · Real-time ADR monitoring
          </span>
        </div>

        {/* Main headline */}
        <h1
          className="text-white max-w-4xl"
          style={{
            fontSize: "clamp(38px, 5.5vw, 68px)",
            fontWeight: 800,
            lineHeight: 1.08,
            letterSpacing: "-0.025em",
          }}
        >
          Detect. Verify. Report.
          <br />
          Drug Safety Signals with{" "}
          <span
            style={{
              background:
                "linear-gradient(125deg, #a5b4fc 0%, #818cf8 40%, #c4b5fd 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
          >
            AlgoPharma
          </span>
        </h1>

        {/* Subtitle */}
        <p
          className="mt-6 max-w-xl"
          style={{
            fontSize: "16px",
            lineHeight: 1.65,
            color: "rgba(255,255,255,0.38)",
            fontWeight: 400,
          }}
        >
          AI-powered pharmacovigilance platform for detecting and analyzing
          adverse drug reactions from social media, forums, and clinical
          discussions in real-time.
        </p>

        {/* Action buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-8">
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 transition-all"
            style={{
              padding: "10px 22px",
              borderRadius: "8px",
              background: "#6366f1",
              color: "white",
              fontSize: "14px",
              fontWeight: 500,
            }}
            onMouseEnter={(e) =>
              ((e.currentTarget as HTMLElement).style.background = "#4f46e5")
            }
            onMouseLeave={(e) =>
              ((e.currentTarget as HTMLElement).style.background = "#6366f1")
            }
          >
            Access Platform <ArrowRight className="w-4 h-4" />
          </button>
          <button
            className="flex items-center gap-2 transition-all"
            style={{
              padding: "10px 22px",
              borderRadius: "8px",
              border: "1px solid rgba(255,255,255,0.10)",
              color: "rgba(255,255,255,0.55)",
              fontSize: "14px",
              fontWeight: 500,
              background: "transparent",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor =
                "rgba(255,255,255,0.18)";
              (e.currentTarget as HTMLElement).style.color =
                "rgba(255,255,255,0.80)";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.borderColor =
                "rgba(255,255,255,0.10)";
              (e.currentTarget as HTMLElement).style.color =
                "rgba(255,255,255,0.55)";
            }}
          >
            View Demo
          </button>
        </div>

        {/* ── Login form (expands inline) ── */}
        {showForm && (
          <div
            className="mt-10 w-full max-w-sm text-left"
            style={{
              background: "rgba(14,14,22,0.85)",
              backdropFilter: "blur(20px)",
              border: "1px solid rgba(255,255,255,0.09)",
              borderRadius: "14px",
              padding: "28px",
            }}
          >
            <h2
              className="text-white/80 mb-5"
              style={{ fontSize: "15px", fontWeight: 600 }}
            >
              Sign in to your account
            </h2>

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label
                  className="block mb-1.5"
                  style={{
                    fontSize: "12px",
                    fontWeight: 500,
                    color: "rgba(255,255,255,0.45)",
                  }}
                >
                  Email address
                </label>
                <div className="relative">
                  <Mail
                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                    style={{ color: "rgba(255,255,255,0.28)" }}
                  />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-9 pr-4 py-2.5 rounded-lg transition-colors focus:outline-none"
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      color: "rgba(255,255,255,0.75)",
                      fontSize: "13px",
                    }}
                    onFocus={(e) =>
                      ((e.currentTarget as HTMLElement).style.borderColor =
                        "rgba(99,102,241,0.5)")
                    }
                    onBlur={(e) =>
                      ((e.currentTarget as HTMLElement).style.borderColor =
                        "rgba(255,255,255,0.08)")
                    }
                  />
                </div>
              </div>

              <div>
                <label
                  className="block mb-1.5"
                  style={{
                    fontSize: "12px",
                    fontWeight: 500,
                    color: "rgba(255,255,255,0.45)",
                  }}
                >
                  Password
                </label>
                <div className="relative">
                  <Lock
                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                    style={{ color: "rgba(255,255,255,0.28)" }}
                  />
                  <input
                    type={showPw ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full pl-9 pr-10 py-2.5 rounded-lg transition-colors focus:outline-none"
                    style={{
                      background: "rgba(255,255,255,0.05)",
                      border: "1px solid rgba(255,255,255,0.08)",
                      color: "rgba(255,255,255,0.75)",
                      fontSize: "13px",
                    }}
                    onFocus={(e) =>
                      ((e.currentTarget as HTMLElement).style.borderColor =
                        "rgba(99,102,241,0.5)")
                    }
                    onBlur={(e) =>
                      ((e.currentTarget as HTMLElement).style.borderColor =
                        "rgba(255,255,255,0.08)")
                    }
                  />
                  <button
                    type="button"
                    onClick={() => setShowPw(!showPw)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 transition-colors"
                    style={{ color: "rgba(255,255,255,0.28)" }}
                  >
                    {showPw ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    className="w-3.5 h-3.5 rounded accent-indigo-500"
                    style={{ background: "rgba(255,255,255,0.05)" }}
                  />
                  <span
                    style={{
                      fontSize: "12px",
                      color: "rgba(255,255,255,0.38)",
                    }}
                  >
                    Remember me
                  </span>
                </label>
                <button
                  type="button"
                  style={{ fontSize: "12px", color: "#818cf8" }}
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full flex items-center justify-center gap-2 rounded-lg py-2.5 transition-all mt-1"
                style={{
                  background: loading ? "rgba(99,102,241,0.6)" : "#6366f1",
                  color: "white",
                  fontSize: "14px",
                  fontWeight: 500,
                }}
                onMouseEnter={(e) => {
                  if (!loading)
                    (e.currentTarget as HTMLElement).style.background =
                      "#4f46e5";
                }}
                onMouseLeave={(e) => {
                  if (!loading)
                    (e.currentTarget as HTMLElement).style.background =
                      "#6366f1";
                }}
              >
                {loading ? (
                  <>
                    <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Signing in…
                  </>
                ) : (
                  "Sign in"
                )}
              </button>
            </form>
          </div>
        )}

        {/* Feature pills */}
        {!showForm && (
          <div className="flex flex-wrap items-center justify-center gap-3 mt-10">
            {[
              { icon: Activity, text: "Real-time signal detection" },
              { icon: TrendingUp, text: "PRR & ROR analytics" },
              { icon: AlertTriangle, text: "ADR severity classification" },
              { icon: FileText, text: "PvPI / VigiFlow export" },
            ].map(({ icon: Icon, text }) => (
              <div
                key={text}
                className="flex items-center gap-2"
                style={{
                  padding: "7px 14px",
                  borderRadius: "100px",
                  border: "1px solid rgba(255,255,255,0.07)",
                  background: "rgba(255,255,255,0.025)",
                  fontSize: "12px",
                  color: "rgba(255,255,255,0.40)",
                }}
              >
                <Icon className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />
                {text}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ══════════════════ DASHBOARD PREVIEW ══════════════════ */}
      <div className="relative z-10 px-6 md:px-12 pb-24">
        <div
          className="mx-auto overflow-hidden"
          style={{
            maxWidth: "900px",
            borderRadius: "14px",
            border: "1px solid rgba(255,255,255,0.09)",
            background: "#0a0a10",
            boxShadow: "0 0 0 1px rgba(0,0,0,0.4), 0 40px 80px rgba(0,0,0,0.6)",
          }}
        >
          {/* Browser chrome */}
          <div
            className="flex items-center gap-2 px-4"
            style={{
              height: "40px",
              borderBottom: "1px solid rgba(255,255,255,0.07)",
              background: "rgba(255,255,255,0.02)",
            }}
          >
            <div className="flex gap-1.5">
              <div className="w-3 h-3 rounded-full" style={{ background: "#ef4444", opacity: 0.6 }} />
              <div className="w-3 h-3 rounded-full" style={{ background: "#f59e0b", opacity: 0.6 }} />
              <div className="w-3 h-3 rounded-full" style={{ background: "#22c55e", opacity: 0.6 }} />
            </div>
            <div
              className="flex-1 mx-3 rounded flex items-center px-3"
              style={{
                height: "24px",
                background: "rgba(255,255,255,0.04)",
                border: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.3)" }}>
                algopharma.in/dashboard
              </span>
            </div>
          </div>

          {/* App UI mockup */}
          <div className="flex" style={{ height: "360px" }}>
            {/* Mini sidebar */}
            <div
              className="flex flex-col shrink-0"
              style={{
                width: "168px",
                borderRight: "1px solid rgba(255,255,255,0.06)",
                padding: "14px 8px",
              }}
            >
              <div className="flex items-center gap-2 px-3 mb-4">
                <div
                  className="w-5 h-5 rounded flex items-center justify-center"
                  style={{ background: "rgba(99,102,241,0.2)" }}
                >
                  <Shield className="w-3 h-3" style={{ color: "#818cf8" }} />
                </div>
                <span style={{ fontSize: "11px", fontWeight: 600, color: "rgba(255,255,255,0.7)" }}>
                  AlgoPharma
                </span>
              </div>
              {[
                { label: "Dashboard", active: true },
                { label: "Signals", active: false },
                { label: "Worklist", active: false },
                { label: "Analytics", active: false },
                { label: "Settings", active: false },
              ].map(({ label, active }) => (
                <div
                  key={label}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-md mb-0.5"
                  style={{
                    background: active ? "rgba(255,255,255,0.09)" : "transparent",
                    fontSize: "11px",
                    fontWeight: active ? 500 : 400,
                    color: active
                      ? "rgba(255,255,255,0.85)"
                      : "rgba(255,255,255,0.38)",
                  }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full"
                    style={{
                      background: active
                        ? "#818cf8"
                        : "rgba(255,255,255,0.15)",
                    }}
                  />
                  {label}
                </div>
              ))}
            </div>

            {/* Main content */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Header bar */}
              <div
                className="flex items-center justify-between px-5 shrink-0"
                style={{
                  height: "42px",
                  borderBottom: "1px solid rgba(255,255,255,0.06)",
                }}
              >
                <div>
                  <span
                    style={{
                      fontSize: "13px",
                      fontWeight: 600,
                      color: "rgba(255,255,255,0.85)",
                    }}
                  >
                    Signal Dashboard
                  </span>
                  <span
                    className="ml-2"
                    style={{
                      fontSize: "10px",
                      color: "rgba(255,255,255,0.30)",
                    }}
                  >
                    Real-time monitoring · Updated just now
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  {[
                    { n: "3", c: "#ef4444" },
                    { n: "3", c: "#f59e0b" },
                    { n: "2", c: "#22c55e" },
                  ].map(({ n, c }, i) => (
                    <div
                      key={i}
                      className="flex items-center gap-1"
                      style={{
                        padding: "2px 7px",
                        borderRadius: "4px",
                        background: `${c}18`,
                        border: `1px solid ${c}30`,
                      }}
                    >
                      <span
                        className="w-1.5 h-1.5 rounded-full"
                        style={{ background: c }}
                      />
                      <span style={{ fontSize: "10px", color: c, fontWeight: 600 }}>
                        {n}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Stat cards row */}
              <div className="grid grid-cols-4 gap-2 px-4 pt-3 pb-2 shrink-0">
                {[
                  { label: "Red Signals", value: "3", color: "#ef4444" },
                  { label: "Amber Signals", value: "3", color: "#f59e0b" },
                  { label: "Green Signals", value: "2", color: "#22c55e" },
                  { label: "Posts Analyzed", value: "1,538", color: "#818cf8" },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    className="rounded-lg px-3 py-2"
                    style={{
                      background: "rgba(255,255,255,0.03)",
                      border: "1px solid rgba(255,255,255,0.06)",
                    }}
                  >
                    <p
                      style={{
                        fontSize: "9px",
                        color: "rgba(255,255,255,0.35)",
                        marginBottom: "3px",
                      }}
                    >
                      {label}
                    </p>
                    <p style={{ fontSize: "16px", fontWeight: 700, color, lineHeight: 1 }}>
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              {/* Table */}
              <div className="flex-1 px-4 overflow-hidden">
                <div
                  className="rounded-lg overflow-hidden"
                  style={{
                    border: "1px solid rgba(255,255,255,0.06)",
                  }}
                >
                  <div
                    className="flex items-center px-3 py-2"
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
                  >
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 600,
                        color: "rgba(255,255,255,0.55)",
                      }}
                    >
                      Top Drugs at Risk
                    </span>
                    <span className="ml-auto flex items-center gap-1" style={{ fontSize: "9px", color: "#818cf8" }}>
                      View worklist <ChevronRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                  <table className="w-full">
                    <thead>
                      <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                        {["Drug", "Symptom", "Sev", "PRR", "Status"].map((h) => (
                          <th
                            key={h}
                            className="text-left px-3 py-1.5"
                            style={{
                              fontSize: "9px",
                              color: "rgba(255,255,255,0.28)",
                              fontWeight: 500,
                            }}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewSignals.map((row, i) => (
                        <tr
                          key={i}
                          style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}
                        >
                          <td
                            className="px-3 py-1.5"
                            style={{
                              fontSize: "10px",
                              fontWeight: 500,
                              color: "rgba(255,255,255,0.75)",
                            }}
                          >
                            {row.drug}
                          </td>
                          <td
                            className="px-3 py-1.5"
                            style={{
                              fontSize: "10px",
                              color: "rgba(255,255,255,0.45)",
                            }}
                          >
                            {row.symptom}
                          </td>
                          <td className="px-3 py-1.5">
                            <SevDot sev={row.sev} />
                          </td>
                          <td
                            className="px-3 py-1.5 font-mono"
                            style={{
                              fontSize: "10px",
                              color: "rgba(255,255,255,0.55)",
                            }}
                          >
                            {row.prr}
                          </td>
                          <td className="px-3 py-1.5">
                            <span
                              style={{
                                fontSize: "9px",
                                fontWeight: 500,
                                padding: "2px 6px",
                                borderRadius: "3px",
                                background:
                                  row.status === "NEW"
                                    ? "rgba(96,165,250,0.15)"
                                    : row.status === "CONFIRMED"
                                    ? "rgba(52,211,153,0.15)"
                                    : "rgba(167,139,250,0.15)",
                                color:
                                  row.status === "NEW"
                                    ? "#60a5fa"
                                    : row.status === "CONFIRMED"
                                    ? "#34d399"
                                    : "#a78bfa",
                              }}
                            >
                              {row.status.replace("_", " ")}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div style={{ height: "10px" }} />
            </div>
          </div>
        </div>

        {/* Bottom labels */}
        <div className="flex justify-center gap-8 mt-6">
          {[
            { label: "74,132", sub: "posts analyzed" },
            { label: "8", sub: "active signals" },
            { label: "97%", sub: "detection accuracy" },
            { label: "CDSCO", sub: "PvPI compliant" },
          ].map(({ label, sub }) => (
            <div key={sub} className="text-center">
              <p
                style={{
                  fontSize: "20px",
                  fontWeight: 700,
                  color: "rgba(255,255,255,0.75)",
                  letterSpacing: "-0.01em",
                }}
              >
                {label}
              </p>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)" }}>
                {sub}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div
        className="relative z-10 text-center pb-8"
        style={{
          fontSize: "12px",
          color: "rgba(255,255,255,0.18)",
          borderTop: "1px solid rgba(255,255,255,0.05)",
          paddingTop: "20px",
        }}
      >
        AlgoPharma v1.0 · CDSCO Compliant · PvPI Ready · Built for Pharmacovigilance Analysts
      </div>
    </div>
  );
}