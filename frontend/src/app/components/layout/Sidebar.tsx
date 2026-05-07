import { useState } from "react";
import { NavLink, useNavigate } from "react-router";
import {
  MessageSquare,
  History,
  BarChart3,
  Settings,
  Bell,
  Activity,
  LogOut,
  User,
  Shield,
  ChevronDown,
  ChevronRight,
  Sparkles,
} from "lucide-react";

const navItems = [
  { icon: MessageSquare, label: "Chat", path: "/chat" },
  { icon: History, label: "History", path: "/history" },
  { icon: BarChart3, label: "Analytics", path: "/analytics" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

const recentChats = [
  { id: 1, text: "Ibuprofen GI Bleeding signal", time: "2h ago" },
  { id: 2, text: "Sertraline suicidal ideation PRR", time: "Yesterday" },
  { id: 3, text: "VigiFlow export status", time: "2d ago" },
];

export function Sidebar() {
  const navigate = useNavigate();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  return (
    <aside
      className="flex flex-col shrink-0 h-screen z-20 relative"
      style={{
        width: "220px",
        background: "rgba(7,7,12,0.75)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderRight: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      {/* ── Logo ── */}
      <div
        className="flex items-center gap-2.5 px-5"
        style={{
          height: "56px",
          borderBottom: "1px solid rgba(255,255,255,0.06)",
        }}
      >
        <div
          className="flex items-center justify-center rounded-lg shrink-0"
          style={{
            width: "28px",
            height: "28px",
            background: "rgba(99,102,241,0.18)",
            border: "1px solid rgba(99,102,241,0.3)",
            backdropFilter: "blur(8px)",
            boxShadow: "0 0 14px rgba(99,102,241,0.2)",
          }}
        >
          <Shield className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />
        </div>
        <div>
          <span
            style={{
              fontSize: "13px",
              fontWeight: 700,
              background: "linear-gradient(90deg, #fff 40%, #818cf8 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              letterSpacing: "-0.01em",
            }}
          >
            AlgoPharma
          </span>
        </div>
        <span
          className="ml-auto px-1.5 py-0.5 rounded"
          style={{
            fontSize: "9px",
            fontWeight: 600,
            background: "rgba(99,102,241,0.12)",
            color: "#818cf8",
            border: "1px solid rgba(99,102,241,0.2)",
            letterSpacing: "0.04em",
          }}
        >
          AI
        </span>
      </div>

      {/* ── New chat button ── */}
      <div className="px-3 pt-3 pb-1">
        <button
          onClick={() => navigate("/chat")}
          className="w-full flex items-center gap-2.5 px-3 py-2.5 rounded-xl transition-all"
          style={{
            fontSize: "12px",
            fontWeight: 600,
            color: "rgba(255,255,255,0.82)",
            background: "rgba(99,102,241,0.14)",
            border: "1px solid rgba(99,102,241,0.25)",
            backdropFilter: "blur(8px)",
            boxShadow: "0 2px 12px rgba(99,102,241,0.12)",
            transition: "all 0.18s ease",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(99,102,241,0.22)";
            (e.currentTarget as HTMLElement).style.boxShadow = "0 4px 18px rgba(99,102,241,0.22)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(99,102,241,0.14)";
            (e.currentTarget as HTMLElement).style.boxShadow = "0 2px 12px rgba(99,102,241,0.12)";
          }}
        >
          <Sparkles className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />
          New Chat
          <ChevronRight className="w-3 h-3 ml-auto opacity-40" style={{ color: "#818cf8" }} />
        </button>
      </div>

      {/* ── Nav ── */}
      <nav className="py-2 px-2.5 space-y-0.5">
        {navItems.map(({ icon: Icon, label, path }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-xl transition-all ${
                isActive
                  ? "text-white/90"
                  : "text-white/38 hover:text-white/68"
              }`
            }
            style={({ isActive }) => ({
              fontSize: "13px",
              fontWeight: 500,
              background: isActive
                ? "rgba(255,255,255,0.075)"
                : "transparent",
              backdropFilter: isActive ? "blur(8px)" : "none",
              border: isActive
                ? "1px solid rgba(255,255,255,0.1)"
                : "1px solid transparent",
              transition: "all 0.15s ease",
            })}
          >
            {({ isActive }) => (
              <>
                <Icon
                  className="w-4 h-4 shrink-0"
                  style={{ color: isActive ? "#818cf8" : undefined }}
                />
                {label}
                {isActive && (
                  <ChevronRight
                    className="w-3 h-3 ml-auto opacity-40"
                    style={{ color: "#818cf8" }}
                  />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* ── Recent chats ── */}
      <div className="px-2.5 pt-1" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <p
          className="px-3 py-2"
          style={{
            fontSize: "10px",
            fontWeight: 600,
            color: "rgba(255,255,255,0.22)",
            letterSpacing: "0.08em",
            textTransform: "uppercase",
          }}
        >
          Recent
        </p>
        {recentChats.map((chat) => (
          <button
            key={chat.id}
            onClick={() => navigate("/chat")}
            className="w-full flex items-start gap-2.5 px-3 py-2 rounded-xl text-left transition-all hover:bg-white/[0.04]"
          >
            <MessageSquare
              className="w-3 h-3 mt-0.5 shrink-0"
              style={{ color: "rgba(255,255,255,0.22)" }}
            />
            <div className="min-w-0">
              <p
                className="truncate"
                style={{ fontSize: "11px", color: "rgba(255,255,255,0.48)" }}
              >
                {chat.text}
              </p>
              <p style={{ fontSize: "10px", color: "rgba(255,255,255,0.22)", marginTop: 2 }}>
                {chat.time}
              </p>
            </div>
          </button>
        ))}
      </div>

      {/* ── Live status ── */}
      <div
        className="px-2.5 py-2 mt-auto"
        style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
      >
        <div
          className="flex items-center gap-2.5 px-3 py-2 rounded-xl"
          style={{
            background: "rgba(34,197,94,0.06)",
            border: "1px solid rgba(34,197,94,0.1)",
          }}
        >
          <Activity className="w-3.5 h-3.5 shrink-0 text-green-400" />
          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.42)" }}>
            5 crawlers active
          </span>
          <span className="ml-auto flex h-1.5 w-1.5 relative">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-500" />
          </span>
        </div>
        <div className="flex items-center gap-2.5 px-3 py-2 mt-0.5 rounded-xl">
          <Bell className="w-3.5 h-3.5 shrink-0 text-amber-400" />
          <span style={{ fontSize: "11px", color: "rgba(255,255,255,0.42)" }}>3 new alerts</span>
          <span
            className="ml-auto px-1.5 py-0.5 rounded-full"
            style={{
              fontSize: "9px",
              fontWeight: 600,
              background: "rgba(245,158,11,0.15)",
              color: "#fbbf24",
              border: "1px solid rgba(245,158,11,0.2)",
            }}
          >
            3
          </span>
        </div>
      </div>

      {/* ── User ── */}
      <div
        className="px-2.5 py-2.5"
        style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
      >
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all"
          style={{
            fontSize: "12px",
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.07)",
            backdropFilter: "blur(8px)",
            transition: "all 0.15s ease",
          }}
          onMouseEnter={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.07)";
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
          }}
        >
          <div
            className="flex items-center justify-center rounded-full shrink-0"
            style={{
              width: "28px",
              height: "28px",
              background: "rgba(99,102,241,0.2)",
              border: "1px solid rgba(99,102,241,0.32)",
            }}
          >
            <User className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />
          </div>
          <div className="text-left min-w-0">
            <p
              className="truncate"
              style={{ fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.78)" }}
            >
              Admin
            </p>
            <p className="truncate" style={{ fontSize: "10px", color: "rgba(255,255,255,0.32)" }}>
              PV Analyst
            </p>
          </div>
          <ChevronDown
            className="w-3 h-3 shrink-0 ml-auto"
            style={{ color: "rgba(255,255,255,0.28)" }}
          />
        </button>

        {userMenuOpen && (
          <div
            className="mt-1 overflow-hidden rounded-xl"
            style={{
              background: "rgba(12,12,20,0.9)",
              backdropFilter: "blur(16px)",
              border: "1px solid rgba(255,255,255,0.1)",
              boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
            }}
          >
            <button
              className="w-full flex items-center gap-2.5 px-4 py-2.5 transition-colors hover:bg-white/[0.05]"
              style={{ fontSize: "12px", color: "rgba(255,255,255,0.55)" }}
            >
              <User className="w-3.5 h-3.5" /> Profile
            </button>
            <button
              onClick={() => navigate("/login")}
              className="w-full flex items-center gap-2.5 px-4 py-2.5 transition-colors hover:bg-white/[0.05]"
              style={{ fontSize: "12px", color: "rgba(239,68,68,0.75)" }}
            >
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
