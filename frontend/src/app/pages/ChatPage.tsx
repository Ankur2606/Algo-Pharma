import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router";
import { motion, AnimatePresence } from "motion/react";
import {
  Send, BookOpen, Pill, Stethoscope, LogOut, User,
  ChevronRight, MessageSquare, Twitter, Globe, Plus,
} from "lucide-react";
import { GlassCard, GlassInner, PageBackground } from "../components/GlassCard";

// ── Requirement-gathering JSON schema ────────────────────────────────────────
// Mirrors the FastAPI backend contract — frontend incrementally fills these
// fields by extracting entities from each user message. When all 3 are filled,
// we POST to the synthesize endpoint and route the user to the dashboard.
interface PVRequest { medicine: string | null; symptom: string | null; source: string | null }

const API = 'http://localhost:8000';

// Real backend call to multi-turn chat endpoint
async function callChatEndpoint(message: string, state: PVRequest): Promise<{ bot_message: string; state: PVRequest; ready?: boolean; project_id?: string }> {
  const res = await fetch(`${API}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, state }),
  });
  if (!res.ok) throw new Error("Failed to fetch from API");
  return res.json();
}

// ── Types ─────────────────────────────────────────────────────────────────────
interface Msg { id: string; role: "user" | "ai"; text: string; tags?: string[] }

// ── Sub-components ────────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex items-center gap-1.5 py-0.5">
      {[0, 1, 2].map((i) => (
        <span key={i} className="rounded-full" style={{
          width: 6, height: 6,
          background: "rgba(100, 200, 255, 0.6)",
          animation: `pvBounce 1.1s ease-in-out ${i * 0.18}s infinite`,
        }} />
      ))}
      <style>{`@keyframes pvBounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}`}</style>
    </div>
  );
}

// Each message exchange: user pill (top-right) + AI reply (bottom-left)
function MessagePair({ userMsg, aiMsg }: { userMsg: Msg; aiMsg: Msg | null }) {
  if (!aiMsg) {
    // Standalone user card (awaiting reply)
    return (
      <GlassCard style={{ padding: "clamp(16px, 2vw, 24px) clamp(18px, 3vw, 28px)" }}>
        <p style={{ fontSize: "clamp(14px, 1.5vw, 16px)", color: "rgba(255,255,255,0.85)", lineHeight: 1.6 }}>{userMsg.text}</p>
      </GlassCard>
    );
  }

  return (
    <GlassCard style={{ padding: "clamp(16px, 2vw, 24px) clamp(18px, 3vw, 28px)" }}>
      {/* User message pill — top right */}
      <div className="flex justify-end mb-4">
        <div style={{
          position: "relative", overflow: "hidden",
          background: "rgba(25,60,100,0.72)",
          backdropFilter: "blur(14px)",
          border: "1px solid rgba(120,200,240,0.20)",
          borderTop: "1px solid rgba(255,255,255,0.22)",
          borderRadius: 10, padding: "clamp(10px, 1.5vw, 14px) clamp(14px, 2vw, 18px)",
          maxWidth: "85%",
          boxShadow: "0 4px 16px rgba(0,0,0,0.35), inset 0 1px 0 rgba(255,255,255,0.08)",
        }}>
          {/* Reflection on user pill */}
          <div style={{
            position: "absolute", inset: 0, borderRadius: "inherit",
            background: "linear-gradient(138deg, rgba(255,255,255,0.10) 0%, transparent 50%)",
            pointerEvents: "none",
          }} />
          <p style={{ position: "relative", fontSize: "clamp(13px, 1.3vw, 15px)", color: "rgba(255,255,255,0.88)", lineHeight: 1.55 }}>
            {userMsg.text}
          </p>
        </div>
      </div>

      {/* AI response */}
      <GlassInner style={{ padding: "clamp(12px, 1.5vw, 18px) clamp(14px, 2vw, 20px)" }}>
        <p className="whitespace-pre-line" style={{ fontSize: "clamp(13px, 1.3vw, 15px)", color: "rgba(255,255,255,0.8)", lineHeight: 1.65 }}>
          {aiMsg.text}
        </p>
      </GlassInner>
    </GlassCard>
  );
}

// Inline attached chips — shown inside the input like Claude's attached skills
function AttachedChips({ activeChips, toggleChip }: { activeChips: string[]; toggleChip: (id: string) => void }) {
  if (!activeChips.length) return null;
  return (
    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {activeChips.map((id) => {
        const cfg = CHIPS_CFG.find((c) => c.id === id);
        if (!cfg) return null;
        const Icon = cfg.Icon;
        return (
          <motion.span
            key={id}
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ duration: 0.18 }}
            style={{
              display: "inline-flex", alignItems: "center", gap: 6,
              padding: "5px 6px 5px 10px", borderRadius: 8,
              fontSize: 12, fontWeight: 500, textTransform: "capitalize",
              color: "#fff",
              background: "rgba(30,100,180,0.55)",
              border: "1px solid rgba(126,200,227,0.5)",
              borderTop: "1px solid rgba(255,255,255,0.32)",
              boxShadow: "0 0 14px rgba(40,150,230,0.3), inset 0 1px 0 rgba(255,255,255,0.18)",
            }}
          >
            <Icon className="w-3 h-3" style={{ color: "#cfeefb" }} />
            {cfg.label}
            <button
              type="button"
              onClick={() => toggleChip(id)}
              style={{
                display: "inline-flex", alignItems: "center", justifyContent: "center",
                width: 16, height: 16, borderRadius: "50%",
                background: "rgba(0,0,0,0.25)", border: "1px solid rgba(255,255,255,0.18)",
                color: "rgba(255,255,255,0.85)", fontSize: 11, fontWeight: 700, lineHeight: 1,
                cursor: "pointer", padding: 0,
              }}
            >×</button>
          </motion.span>
        );
      })}
    </div>
  );
}

// Closeable chip node
function ChipNode({ label, Icon, active, onToggle }: {
  label: string; Icon: React.ElementType; active: boolean; onToggle: () => void;
}) {
  return (
    <button
      onClick={onToggle}
      style={{
        position: "relative", overflow: "hidden",
        padding: active ? "8px 10px 8px 14px" : "8px 18px",
        borderRadius: 12, fontSize: "clamp(12px, 1.2vw, 14px)", fontWeight: 500,
        color: active ? "rgba(210,240,255,0.95)" : "rgba(200,225,245,0.72)",
        background: active ? "rgba(30,90,160,0.45)" : "rgba(12,30,55,0.55)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(120,200,240,0.14)",
        borderTop: active ? "1px solid rgba(255,255,255,0.28)" : "1px solid rgba(255,255,255,0.18)",
        boxShadow: active
          ? "0 0 20px rgba(40,130,210,0.22), inset 0 1px 0 rgba(255,255,255,0.08)"
          : "inset 0 1px 0 rgba(255,255,255,0.06)",
        transition: "all 0.2s ease",
        display: "flex", alignItems: "center", gap: 8,
        whiteSpace: "nowrap",
      }}
    >
      {/* Chip reflection */}
      <div style={{
        position: "absolute", inset: 0, borderRadius: "inherit",
        background: "linear-gradient(138deg, rgba(255,255,255,0.09) 0%, transparent 50%)",
        pointerEvents: "none",
      }} />
      <Icon className="w-4 h-4 shrink-0" style={{ position: "relative" }} />
      <span style={{ position: "relative" }}>{label}</span>
      {active && (
        <span className="flex items-center justify-center rounded-full shrink-0" style={{
          position: "relative",
          width: 18, height: 18,
          background: "rgba(50,120,200,0.5)",
          border: "1px solid rgba(120,200,240,0.4)",
          fontSize: 12, color: "rgba(200,235,255,0.9)", fontWeight: 700, lineHeight: 1,
        }}>×</span>
      )}
    </button>
  );
}

// Welcome suggestion cards — quick-fill examples for the gathering flow
const SUGGESTIONS = [
  { icon: Pill, label: "Ibuprofen", sub: "Start with a medicine", color: "#7ec8e3" },
  { icon: Stethoscope, label: "GI bleeding", sub: "Start with a symptom", color: "#ef4444" },
  { icon: BookOpen, label: "Reddit", sub: "Start with a source", color: "#22c55e" },
  { icon: MessageSquare, label: "Ibuprofen GI bleeding Reddit", sub: "Fill all three at once", color: "#f59e0b" },
];

const CHIPS_CFG = [
  { id: "source", label: "source", Icon: BookOpen },
  { id: "medicine", label: "medicine", Icon: Pill },
  { id: "symptom", label: "symptom", Icon: Stethoscope },
];

// ── Main ──────────────────────────────────────────────────────────────────────
export function ChatPage() {
  const navigate = useNavigate();
  const INITIAL_AI: Msg = {
    id: "ai-greet",
    role: "ai",
    text: "Tell me a medicine, symptom, and source to get started.",
    tags: [],
  };
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [activeChips, setActiveChips] = useState<string[]>([]);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [pvRequest, setPvRequest] = useState<PVRequest>({ medicine: null, symptom: null, source: null });
  const [synthesizing, setSynthesizing] = useState(false);
  const [inputFocused, setInputFocused] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages, isTyping]);

  const toggleChip = (id: string) =>
    setActiveChips((p) => p.includes(id) ? p.filter((c) => c !== id) : [...p, id]);

  const sendMessage = (text: string) => {
    if (!text.trim()) return;
    const cleanText = text.trim();
    const userMsg: Msg = { id: crypto.randomUUID(), role: "user", text: cleanText };

    const attached = [...activeChips];
    setMessages((p) => [...p, userMsg]);
    setInput(""); setActiveChips([]); setIsTyping(true);

    setTimeout(async () => {
      try {
        const data = await callChatEndpoint(cleanText, pvRequest);
        setPvRequest(data.state || pvRequest);
        
        if (data.ready || data.bot_message === "READY") {
          setMessages((p) => [...p, { id: crypto.randomUUID(), role: "ai", text: "✅ Analysis starting..." }]);
          setSynthesizing(true);
          setTimeout(() => navigate(`/processing?project_id=${data.project_id || ''}`, { state: data.state }), 3000);
        } else {
          setMessages((p) => [...p, { id: crypto.randomUUID(), role: "ai", text: data.bot_message }]);
        }
      } catch (err) {
        setMessages((p) => [...p, { id: crypto.randomUUID(), role: "ai", text: "⚠️ Could not reach the server. Make sure AlgoPharma API is running on port 8000." }]);
      } finally {
        setIsTyping(false);
      }
    }, 500);
  };

  const attachChipsRow = (
    <div style={{ display: "flex", gap: 6, justifyContent: "center", flexWrap: "wrap" }}>
      {CHIPS_CFG.map(({ id, label, Icon }) => {
        const attached = activeChips.includes(id);
        return (
          <button
            key={id}
            type="button"
            onClick={() => toggleChip(id)}
            style={{
              display: "inline-flex", alignItems: "center", gap: 5,
              padding: "6px 12px",
              borderRadius: 6,
              fontSize: 11, fontWeight: 500,
              textTransform: "capitalize",
              color: attached ? "#fff" : "rgba(200,225,245,0.7)",
              background: attached ? "rgba(59,130,246,0.25)" : "rgba(255,255,255,0.04)",
              border: attached ? "1px solid rgba(99,180,255,0.4)" : "1px solid rgba(255,255,255,0.1)",
              cursor: "pointer",
              transition: "all 0.2s ease",
            }}
          >
            <Icon className="w-3 h-3" />
            {label}
            {attached && <Plus className="w-3 h-3" />}
          </button>
        );
      })}
    </div>
  );

  // Group into user+ai pairs
  const pairs: { user: Msg; ai: Msg | null }[] = [];
  for (let i = 0; i < messages.length; i++) {
    if (messages[i].role === "user") {
      const ai = messages[i + 1]?.role === "ai" ? messages[i + 1] : null;
      pairs.push({ user: messages[i], ai }); if (ai) i++;
    }
  }

  return (
    <PageBackground>
      {/* ── Header ── */}
      <header style={{
        position: "sticky", top: 0, zIndex: 30,
        display: "flex", alignItems: "center", padding: "0 clamp(14px, 2vw, 24px)", height: "clamp(48px, 8vw, 56px)",
        background: "rgba(0, 0, 0, 0.6)",
        backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        borderTop: "none",
        boxShadow: "none",
      }}>
        <span style={{
          fontSize: "clamp(12px, 1.8vw, 16px)", fontWeight: 700, letterSpacing: "-0.01em",
          color: "#fff",
          position: "relative",
        }}>AlgoPharma</span>

        {messages.length > 0 && (
          <button onClick={() => { setMessages([]); setPvRequest({ medicine: null, symptom: null, source: null }); setInput(""); }} className="ml-4 px-2.5 py-1 rounded-lg" style={{
            fontSize: 11, color: "rgba(126,200,227,0.55)",
            border: "1px solid rgba(100,180,220,0.12)",
            background: "rgba(15,45,80,0.4)",
            position: "relative",
          }}>New chat</button>
        )}

        {/* User menu */}
        <div className="ml-auto relative" style={{ zIndex: 40 }}>
          <button onClick={() => setUserMenuOpen(!userMenuOpen)} style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "6px 12px", borderRadius: 10,
            background: "rgba(15,40,75,0.55)",
            border: "1px solid rgba(120,200,240,0.12)",
            borderTop: "1px solid rgba(255,255,255,0.14)",
            backdropFilter: "blur(10px)",
          }}>
            <div className="flex items-center justify-center rounded-full" style={{
              width: 22, height: 22,
              background: "rgba(30,90,160,0.5)",
              border: "1px solid rgba(120,200,240,0.3)",
            }}>
              <User className="w-3 h-3" style={{ color: "#7ec8e3" }} />
            </div>
            <span style={{ fontSize: 12, fontWeight: 500, color: "rgba(255,255,255,0.72)" }}>Admin</span>
          </button>
          {userMenuOpen && (
            <div style={{
              position: "absolute", right: 0, top: "calc(100% + 8px)",
              background: "rgba(6,18,36,0.95)", backdropFilter: "blur(20px)",
              border: "1px solid rgba(120,200,240,0.14)",
              borderTop: "1px solid rgba(255,255,255,0.16)",
              borderRadius: 12, minWidth: 140,
              boxShadow: "0 12px 40px rgba(0,0,0,0.6)",
              overflow: "hidden",
            }}>
              <div style={{
                position: "absolute", inset: 0,
                background: "linear-gradient(138deg, rgba(255,255,255,0.05) 0%, transparent 40%)",
                pointerEvents: "none",
              }} />
              <button className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/[0.05]" style={{ fontSize: 13, color: "rgba(255,255,255,0.55)", position: "relative" }}>
                <User className="w-3.5 h-3.5" /> Profile
              </button>
              <button onClick={() => navigate("/")} className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/[0.05]" style={{ fontSize: 13, color: "rgba(239,68,68,0.75)", position: "relative" }}>
                <LogOut className="w-3.5 h-3.5" /> Sign out
              </button>
            </div>
          )}
        </div>
      </header>

      {/* ── Scroll area ── */}
      <div style={{ overflowY: "auto", scrollbarWidth: "thin", scrollbarColor: "rgba(100,180,220,0.1) transparent", display: messages.length ? "block" : "none" }}>
        <div style={{ maxWidth: "min(1000px, 90vw)", margin: "0 auto", padding: "32px clamp(16px, 3vw, 32px) 220px", display: "flex", flexDirection: "column", gap: 14 }}>

          {/* Standalone AI greeting once the chat starts */}
          {messages.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
              <GlassCard style={{ padding: "clamp(14px, 2vw, 20px) clamp(16px, 3vw, 24px)" }}>
                <p style={{ fontSize: "clamp(13px, 1.3vw, 14px)", color: "rgba(255,255,255,0.8)", lineHeight: 1.6 }}>{INITIAL_AI.text}</p>
              </GlassCard>
            </motion.div>
          )}

          {/* Message pairs */}
          <AnimatePresence initial={false}>
            {pairs.map(({ user, ai }) => (
              <motion.div
                key={user.id}
                initial={{ opacity: 0, y: 14 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              >
                <MessagePair userMsg={user} aiMsg={ai} />
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Dynamic source suggestion chips — appear when source is the only missing field */}
          {messages.length > 0 && pvRequest.medicine && pvRequest.symptom && !pvRequest.source && !isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.1 }}
              style={{ display: "flex", flexWrap: "wrap", gap: "clamp(6px, 1.5vw, 10px)", paddingLeft: "clamp(30px, 5vw, 60px)" }}
            >
              {[
                { label: "Reddit", Icon: MessageSquare },
                { label: "Twitter", Icon: Twitter },
                { label: "Custom forum", Icon: Globe },
              ].map(({ label, Icon }) => (
                <motion.button
                  key={label}
                  whileHover={{ y: -2 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => sendMessage(label)}
                  style={{
                    position: "relative", overflow: "hidden",
                    display: "flex", alignItems: "center", gap: 8,
                    padding: "clamp(6px, 1.2vw, 10px) clamp(10px, 1.8vw, 16px)", borderRadius: 10, fontSize: "clamp(11px, 1.3vw, 13px)", fontWeight: 500,
                    color: "#ffffff",
                    background: "rgba(30, 30, 40, 0.5)",
                    border: "1px solid rgba(100, 150, 200, 0.2)",
                    borderTop: "1px solid rgba(255,255,255,0.1)",
                    backdropFilter: "blur(8px)",
                    boxShadow: "0 0 12px rgba(59, 130, 246, 0.1), inset 0 1px 0 rgba(255,255,255,0.05)",
                    cursor: "pointer",
                  }}
                >
                  <Icon className="w-3.5 h-3.5" style={{ color: "#7ec8e3" }} />
                  {label}
                </motion.button>
              ))}
            </motion.div>
          )}

          {/* Typing */}
          {isTyping && (
            <GlassCard style={{ padding: "16px 20px" }}>
              <div className="flex items-center gap-3">
                <TypingDots />
              </div>
            </GlassCard>
          )}

          <div ref={endRef} />
        </div>
      </div>

      {messages.length === 0 ? (
        // ─────────── EMPTY STATE — fullscreen centered hero box ───────────
        <div style={{
          position: "fixed", left: 0, right: 0, top: 52, bottom: 0, zIndex: 10,
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: "clamp(16px, 3vw, 32px)",
          overflowY: "auto",
        }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            style={{ width: "100%", maxWidth: "min(800px, 95vw)", display: "flex", flexDirection: "column", alignItems: "center", textAlign: "center" }}
          >
            <p style={{ fontSize: "clamp(13px, 1.8vw, 15px)", color: "#ffffff", maxWidth: 520, lineHeight: 1.6, marginBottom: 24, opacity: 0.7 }}>
              Share a medicine, symptom, and source
            </p>

            {/* Attachable field buttons — click to attach like a skill in Claude */}
            {/* THE CENTERED CHAT BOX — large, prominent, single input */}
            <motion.div
              animate={{
                boxShadow: inputFocused
                  ? "0 0 0 1px rgba(126,200,227,0.55), 0 0 60px rgba(40,130,210,0.35)"
                  : "0 0 0 1px rgba(126,200,227,0.18), 0 0 40px rgba(40,130,210,0.18)",
              }}
              transition={{ duration: 0.3 }}
              style={{ borderRadius: 8, width: "100%", maxWidth: "clamp(300px, 90vw, 720px)" }}
            >
              <GlassCard style={{ padding: 0, borderRadius: 8 }}>
                <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
                  style={{ display: "flex", flexDirection: "column", gap: 10, padding: "clamp(14px, 2vw, 22px) clamp(16px, 2.5vw, 28px)" }}>
                  {attachChipsRow}
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <input
                    autoFocus
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onFocus={() => setInputFocused(true)}
                    onBlur={() => setInputFocused(false)}
                    placeholder="Type a medicine, symptom, or source..."
                    style={{
                      flex: 1, minWidth: 120, background: "transparent", outline: "none", border: "none",
                      fontSize: "clamp(13px, 1.5vw, 15px)", color: "rgba(255,255,255,0.9)",
                      minHeight: "42px", display: "flex", alignItems: "center",
                    }}
                  />
                  <motion.button
                    whileHover={input.trim() ? { scale: 1.08 } : {}}
                    whileTap={input.trim() ? { scale: 0.92 } : {}}
                    type="submit"
                    disabled={!input.trim() || isTyping}
                    style={{
                      position: "relative", overflow: "hidden",
                      width: "clamp(40px, 6vw, 48px)", height: "clamp(40px, 6vw, 48px)", borderRadius: 8, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      background: input.trim() ? "rgba(30,100,180,0.85)" : "rgba(15,35,65,0.5)",
                      border: "1px solid rgba(120,200,240,0.24)",
                      borderTop: input.trim() ? "1px solid rgba(255,255,255,0.3)" : "1px solid rgba(255,255,255,0.1)",
                      boxShadow: input.trim() ? "0 0 28px rgba(40,150,230,0.5)" : "none",
                      cursor: input.trim() ? "pointer" : "not-allowed",
                      transition: "background 0.2s ease, box-shadow 0.2s ease",
                    }}
                  >
                    <div style={{ position: "absolute", inset: 0, borderRadius: "inherit", background: "linear-gradient(138deg, rgba(255,255,255,0.14) 0%, transparent 50%)", pointerEvents: "none" }} />
                    <Send className="w-5 h-5" style={{
                      color: input.trim() ? "#fff" : "rgba(100,160,210,0.4)", position: "relative",
                    }} />
                  </motion.button>
                  </div>
                </form>
                {activeChips.length > 0 && (
                  <div style={{ padding: "0 clamp(16px, 2.5vw, 28px) clamp(14px, 2vw, 18px)" }}>
                    <AttachedChips activeChips={activeChips} toggleChip={toggleChip} />
                  </div>
                )}
              </GlassCard>
            </motion.div>


          </motion.div>
        </div>
      ) : (
        // ─────────── ACTIVE CHAT — fixed bottom composer (matches hero box) ───────────
        <div style={{
          position: "fixed", left: 0, right: 0, bottom: 0, zIndex: 30,
          padding: "clamp(12px, 2vw, 20px) clamp(12px, 3vw, 20px)",
          background: "transparent",
          pointerEvents: "none",
        }}>
          <div style={{ maxWidth: "min(1000px, 90vw)", margin: "0 auto", display: "flex", flexDirection: "column", gap: 8, pointerEvents: "auto" }}>
            {/* Attach-skill row (compact) */}
            <motion.div
              animate={{
                boxShadow: inputFocused
                  ? "0 0 0 1px rgba(126,200,227,0.55), 0 0 60px rgba(40,130,210,0.35)"
                  : "0 0 0 1px rgba(126,200,227,0.18), 0 0 40px rgba(40,130,210,0.18)",
              }}
              transition={{ duration: 0.3 }}
              style={{ borderRadius: 8 }}
            >
              <GlassCard style={{ padding: 0, borderRadius: 8 }}>
                <form onSubmit={(e) => { e.preventDefault(); sendMessage(input); }} style={{ display: "flex", flexDirection: "column", gap: 10, padding: "clamp(12px, 1.5vw, 20px) clamp(14px, 2.5vw, 24px)" }}>
                  {attachChipsRow}
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onFocus={() => setInputFocused(true)}
                    onBlur={() => setInputFocused(false)}
                    placeholder={activeChips.length ? `Type the ${activeChips.join(" / ")} value...` : "Type your medicine, symptom, or source..."}
                    style={{ flex: 1, minWidth: 120, background: "transparent", outline: "none", border: "none", fontSize: "clamp(14px, 1.5vw, 16px)", color: "rgba(220,235,255,0.92)", minHeight: "40px" }}
                  />
                  <motion.button
                    whileHover={input.trim() && !isTyping ? { scale: 1.08 } : {}}
                    whileTap={input.trim() && !isTyping ? { scale: 0.92 } : {}}
                    type="submit"
                    disabled={!input.trim() || isTyping}
                    style={{
                      position: "relative", overflow: "hidden",
                      width: "clamp(38px, 5vw, 44px)", height: "clamp(38px, 5vw, 44px)", borderRadius: 8, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      background: input.trim() && !isTyping ? "rgba(30,100,180,0.85)" : "rgba(15,35,65,0.5)",
                      border: "1px solid rgba(120,200,240,0.24)",
                      borderTop: input.trim() && !isTyping ? "1px solid rgba(255,255,255,0.3)" : "1px solid rgba(255,255,255,0.1)",
                      boxShadow: input.trim() && !isTyping ? "0 0 24px rgba(40,150,230,0.5)" : "none",
                      cursor: input.trim() && !isTyping ? "pointer" : "not-allowed",
                      transition: "background 0.2s ease, box-shadow 0.2s ease",
                    }}
                  >
                    <div style={{ position: "absolute", inset: 0, borderRadius: "inherit", background: "linear-gradient(138deg, rgba(255,255,255,0.14) 0%, transparent 50%)", pointerEvents: "none" }} />
                    <Send className="w-4 h-4" style={{ color: input.trim() && !isTyping ? "#fff" : "rgba(100,160,210,0.4)", position: "relative" }} />
                  </motion.button>
                  </div>
                </form>
                {activeChips.length > 0 && (
                  <div style={{ padding: "0 clamp(14px, 2.5vw, 24px) clamp(10px, 1.5vw, 16px)" }}>
                    <AttachedChips activeChips={activeChips} toggleChip={toggleChip} />
                  </div>
                )}
              </GlassCard>
            </motion.div>


          </div>
        </div>
      )}



      {/* Synthesizing overlay — shown while FastAPI/LLM call resolves */}
      <AnimatePresence>
        {synthesizing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35 }}
            style={{
              position: "fixed", inset: 0, zIndex: 100,
              background: "rgba(4,10,20,0.78)",
              backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}
          >
            <motion.div
              initial={{ scale: 0.96, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
              style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}
            >
              <div style={{ position: "relative", width: 120, height: 120 }}>
                {[0, 1, 2, 3].map((i) => (
                  <motion.div
                    key={i}
                    animate={{ rotate: 360 }}
                    transition={{ duration: 4 + i * 0.8, repeat: Infinity, ease: "linear" }}
                    style={{
                      position: "absolute", inset: i * 8, borderRadius: "50%",
                      border: "1px solid transparent",
                      borderTopColor: `rgba(126,200,227,${0.55 - i * 0.1})`,
                      borderRightColor: `rgba(40,130,210,${0.4 - i * 0.08})`,
                    }}
                  />
                ))}
              </div>
              <div style={{ textAlign: "center" }}>
                <p style={{
                  fontSize: 18, fontWeight: 700, letterSpacing: "-0.01em",
                  background: "linear-gradient(110deg,#fff 30%,#7ec8e3 100%)",
                  WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent",
                  marginBottom: 8,
                }}>Synthesizing insights…</p>
                <p style={{ fontSize: 12, color: "rgba(200,225,245,0.5)" }}>
                  Aggregating signals from {pvRequest.source} · analyzing {pvRequest.medicine} · {pvRequest.symptom}
                </p>
              </div>
              <div style={{ width: 220, height: 2, borderRadius: 2, background: "rgba(126,200,227,0.12)", overflow: "hidden" }}>
                <motion.div
                  initial={{ x: "-100%" }}
                  animate={{ x: "100%" }}
                  transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
                  style={{ width: "60%", height: "100%", background: "linear-gradient(90deg, transparent, rgba(126,200,227,0.85), transparent)" }}
                />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageBackground>
  );
}
