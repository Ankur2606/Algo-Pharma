import { useState } from "react";
import { useNavigate } from "react-router";
import { Shield, Eye, EyeOff, ArrowRight, Mail, Lock, User } from "lucide-react";
import { GlassCard, PageBackground } from "../components/GlassCard";

const glassInput: React.CSSProperties = {
  position: "relative",
  background: "rgba(8,22,44,0.65)",
  backdropFilter: "blur(12px)",
  border: "1px solid rgba(120,200,240,0.14)",
  borderTop: "1px solid rgba(255,255,255,0.16)",
  borderRadius: 10,
  color: "rgba(220,235,255,0.85)",
  fontSize: 14,
  outline: "none",
  width: "100%",
  padding: "12px 14px 12px 42px",
  transition: "border-color 0.2s, box-shadow 0.2s",
  boxShadow: "inset 0 1px 0 rgba(255,255,255,0.04)",
};

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPw, setShowPw] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => navigate("/chat"), 950);
  };

  return (
    <PageBackground>
      <div style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px 16px",
      }}>
        {/* ── Brand logo ── */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 36 }}>
          <div style={{
            position: "relative", overflow: "hidden",
            width: 48, height: 48, flexShrink: 0,
            display: "flex", alignItems: "center", justifyContent: "center",
            borderRadius: 14,
            background: "rgba(20,70,150,0.38)",
            border: "1px solid rgba(120,200,240,0.22)",
            borderTop: "1px solid rgba(255,255,255,0.30)",
            backdropFilter: "blur(10px)",
            boxShadow: "0 0 30px rgba(30,120,210,0.22), inset 0 1px 0 rgba(255,255,255,0.12)",
          }}>
            {/* Reflection on logo */}
            <div style={{
              position: "absolute", inset: 0, borderRadius: "inherit",
              background: "linear-gradient(138deg, rgba(255,255,255,0.14) 0%, transparent 50%)",
              pointerEvents: "none",
            }} />
            <Shield className="w-6 h-6" style={{ color: "#7ec8e3", position: "relative" }} />
          </div>
          <div>
            <h1 style={{
              fontSize: 24, fontWeight: 900, letterSpacing: "-0.025em",
              background: "linear-gradient(110deg,#ffffff 35%,#7ec8e3 100%)",
              WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
              lineHeight: 1.1, marginBottom: 2,
            }}>AlgoPharma</h1>
            <p style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.14em", color: "rgba(126,200,227,0.5)" }}>
              PHARMACOVIGILANCE AI
            </p>
          </div>
        </div>

        {/* ── Auth card ── */}
        <GlassCard bright style={{ width: "100%", maxWidth: 400, padding: "30px 30px 26px" }}>
          {/* Tab switcher */}
          <div style={{
            display: "flex", padding: 4, borderRadius: 12, marginBottom: 26,
            background: "rgba(5,18,38,0.7)",
            border: "1px solid rgba(120,200,240,0.1)",
            borderTop: "1px solid rgba(255,255,255,0.08)",
          }}>
            {(["signin", "signup"] as const).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                style={{
                  position: "relative", overflow: "hidden",
                  flex: 1, padding: "8px 0", borderRadius: 8,
                  fontSize: 13, fontWeight: 600,
                  color: mode === m ? "rgba(220,240,255,0.92)" : "rgba(200,225,245,0.35)",
                  background: mode === m ? "rgba(25,80,155,0.45)" : "transparent",
                  border: mode === m ? "1px solid rgba(120,200,240,0.22)" : "1px solid transparent",
                  borderTop: mode === m ? "1px solid rgba(255,255,255,0.20)" : "1px solid transparent",
                  backdropFilter: mode === m ? "blur(8px)" : "none",
                  boxShadow: mode === m ? "0 2px 16px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.07)" : "none",
                  transition: "all 0.2s ease",
                  cursor: "pointer",
                }}
              >
                {mode === m && (
                  <div style={{
                    position: "absolute", inset: 0, borderRadius: "inherit",
                    background: "linear-gradient(138deg, rgba(255,255,255,0.09) 0%, transparent 50%)",
                    pointerEvents: "none",
                  }} />
                )}
                <span style={{ position: "relative" }}>{m === "signin" ? "Sign In" : "Sign Up"}</span>
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {/* Name (signup only) */}
            {mode === "signup" && (
              <div style={{ position: "relative" }}>
                <User className="w-4 h-4" style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", color: "rgba(126,200,227,0.45)", pointerEvents: "none" }} />
                <input
                  type="text" placeholder="Full name"
                  value={name} onChange={(e) => setName(e.target.value)}
                  style={glassInput}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(100,180,220,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(40,120,200,0.12), inset 0 1px 0 rgba(255,255,255,0.04)"; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(120,200,240,0.14)"; e.currentTarget.style.boxShadow = "inset 0 1px 0 rgba(255,255,255,0.04)"; }}
                />
              </div>
            )}

            {/* Email */}
            <div style={{ position: "relative" }}>
              <Mail className="w-4 h-4" style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", color: "rgba(126,200,227,0.45)", pointerEvents: "none" }} />
              <input
                type="email" placeholder="Email address"
                value={email} onChange={(e) => setEmail(e.target.value)}
                style={glassInput}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(100,180,220,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(40,120,200,0.12), inset 0 1px 0 rgba(255,255,255,0.04)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(120,200,240,0.14)"; e.currentTarget.style.boxShadow = "inset 0 1px 0 rgba(255,255,255,0.04)"; }}
              />
            </div>

            {/* Password */}
            <div style={{ position: "relative" }}>
              <Lock className="w-4 h-4" style={{ position: "absolute", left: 13, top: "50%", transform: "translateY(-50%)", color: "rgba(126,200,227,0.45)", pointerEvents: "none" }} />
              <input
                type={showPw ? "text" : "password"} placeholder="Password"
                value={password} onChange={(e) => setPassword(e.target.value)}
                style={{ ...glassInput, paddingRight: 44 }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "rgba(100,180,220,0.4)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(40,120,200,0.12), inset 0 1px 0 rgba(255,255,255,0.04)"; }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "rgba(120,200,240,0.14)"; e.currentTarget.style.boxShadow = "inset 0 1px 0 rgba(255,255,255,0.04)"; }}
              />
              <button type="button" onClick={() => setShowPw(!showPw)} style={{ position: "absolute", right: 13, top: "50%", transform: "translateY(-50%)", color: "rgba(126,200,227,0.4)", background: "none", border: "none", cursor: "pointer" }}>
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              style={{
                position: "relative", overflow: "hidden",
                width: "100%", marginTop: 4,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                padding: "13px 20px", borderRadius: 11,
                fontSize: 14, fontWeight: 700, color: "#fff",
                background: loading
                  ? "rgba(25,80,155,0.45)"
                  : "linear-gradient(120deg, rgba(25,90,175,0.9) 0%, rgba(40,130,210,0.9) 100%)",
                border: "1px solid rgba(120,200,240,0.3)",
                borderTop: "1px solid rgba(255,255,255,0.28)",
                boxShadow: loading ? "none" : "0 6px 28px rgba(30,110,200,0.32), inset 0 1px 0 rgba(255,255,255,0.15)",
                backdropFilter: "blur(8px)",
                cursor: loading ? "not-allowed" : "pointer",
                transition: "all 0.2s ease",
              }}
              onMouseEnter={(e) => { if (!loading) (e.currentTarget as HTMLElement).style.boxShadow = "0 8px 36px rgba(30,110,200,0.48), inset 0 1px 0 rgba(255,255,255,0.18)"; }}
              onMouseLeave={(e) => { if (!loading) (e.currentTarget as HTMLElement).style.boxShadow = "0 6px 28px rgba(30,110,200,0.32), inset 0 1px 0 rgba(255,255,255,0.15)"; }}
            >
              {/* Button reflection */}
              <div style={{ position: "absolute", inset: 0, borderRadius: "inherit", background: "linear-gradient(138deg, rgba(255,255,255,0.13) 0%, transparent 50%)", pointerEvents: "none" }} />
              {loading
                ? <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" style={{ position: "relative" }} />
                : <>
                    <span style={{ position: "relative" }}>{mode === "signin" ? "Sign In" : "Create Account"}</span>
                    <ArrowRight className="w-4 h-4" style={{ position: "relative" }} />
                  </>
              }
            </button>
          </form>

          {/* Toggle link */}
          <p style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "rgba(200,225,245,0.35)" }}>
            {mode === "signin" ? "Don't have an account?" : "Already have an account?"}{" "}
            <button
              onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
              style={{ color: "#7ec8e3", fontWeight: 600, background: "none", border: "none", cursor: "pointer" }}
            >
              {mode === "signin" ? "Sign up" : "Sign in"}
            </button>
          </p>
        </GlassCard>

        {/* Feature pills */}
        <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 10, marginTop: 28, maxWidth: 400 }}>
          {["CDSCO Compliant", "PvPI Ready", "VigiBase Sync", "5 Active Crawlers"].map((label) => (
            <span key={label} style={{
              padding: "5px 12px", borderRadius: 100,
              fontSize: 11, fontWeight: 500,
              color: "rgba(200,225,245,0.38)",
              background: "rgba(10,28,55,0.5)",
              border: "1px solid rgba(120,200,240,0.1)",
              borderTop: "1px solid rgba(255,255,255,0.08)",
              backdropFilter: "blur(8px)",
            }}>{label}</span>
          ))}
        </div>
      </div>
    </PageBackground>
  );
}