import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { Header } from "../components/layout/Header";
import { SeverityBadge } from "../components/shared/SeverityBadge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { signals, timelineData, activityFeed } from "../data/mockData";
import {
  AlertTriangle,
  TrendingUp,
  FileText,
  Activity,
  ChevronRight,
  ExternalLink,
  ArrowUpRight,
  Loader2,
} from "lucide-react";

const API = 'http://localhost:8000';

interface Signal { id: string; drug: string; symptom: string; ror: number; prr: number; chi2: number; postCount: number; strength: "STRONG" | "MODERATE" | "WEAK"; status: string }
interface Post { platform: string; sentiment: string; ae_flag: boolean; text: string; ae_confidence: number; ae_reason: string }

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div
        className="rounded-lg p-3 text-xs shadow-2xl"
        style={{
          background: "#111118",
          border: "1px solid rgba(255,255,255,0.10)",
        }}
      >
        <p className="mb-2" style={{ color: "rgba(255,255,255,0.50)" }}>
          {label}
        </p>
        {payload.map((p: any, i: number) => (
          <div key={p.dataKey || p.name || `tooltip-item-${i}`} className="flex items-center gap-2 py-0.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: p.color }}
            />
            <span
              className="capitalize"
              style={{ color: "rgba(255,255,255,0.60)" }}
            >
              {p.name}:
            </span>
            <span style={{ color: "rgba(255,255,255,0.88)", fontWeight: 600 }}>
              {p.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const hrs = Math.floor(diff / 3600000);
  if (hrs < 1) return "< 1h ago";
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// Card component for stat cards
function StatCard({
  label,
  value,
  icon: Icon,
  color,
  bg,
  border,
  sub,
}: {
  label: string;
  value: string | number;
  icon: React.ElementType;
  color: string;
  bg: string;
  border: string;
  sub: string;
}) {
  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-3"
      style={{
        background: "#0c0c14",
        border: `1px solid ${border}`,
      }}
    >
      <div className="flex items-start justify-between">
        <p
          style={{
            fontSize: "12px",
            fontWeight: 500,
            color: "rgba(255,255,255,0.40)",
          }}
        >
          {label}
        </p>
        <div
          className="flex items-center justify-center rounded-lg"
          style={{ width: "32px", height: "32px", background: bg }}
        >
          <Icon className="w-4 h-4" style={{ color }} />
        </div>
      </div>
      <p
        style={{
          fontSize: "30px",
          fontWeight: 700,
          color,
          lineHeight: 1,
          letterSpacing: "-0.02em",
        }}
      >
        {value}
      </p>
      <p style={{ fontSize: "11px", color: "rgba(255,255,255,0.28)" }}>{sub}</p>
    </div>
  );
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const projectId = searchParams.get("project_id");

  const [dashboardStatus, setDashboardStatus] = useState("crawling");
  const [realSignals, setRealSignals] = useState<Signal[]>([]);
  const [realPosts, setRealPosts] = useState<Post[]>([]);

  useEffect(() => {
    if (!projectId) return;
    let pollCount = 0;
    const interval = setInterval(async () => {
      try {
        const token = localStorage.getItem("token") || "";
        const headers: HeadersInit = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const res = await fetch(`${API}/api/results/${projectId}`, { headers });
        if (!res.ok) return;
        const data = await res.json();
        
        setDashboardStatus(data.status);
        if (data.signals) {
          setRealSignals(data.signals.map((s: any) => ({
            id: s.drug + s.symptom,
            drug: s.drug,
            symptom: s.symptom,
            postCount: s.post_count,
            prr: s.prr,
            ror: s.ror,
            chi2: s.chi_square,
            strength: s.strength,
            status: "Active"
          })));
        }
        if (data.posts) {
          setRealPosts(data.posts);
        }

        if (data.status === 'complete' || pollCount > 75) {
          clearInterval(interval);
        }
        pollCount++;
      } catch (err) {
        console.warn("Poll failed", err);
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [projectId]);

  const redSignals = realSignals.filter((s) => s.strength === "STRONG");
  const amberSignals = realSignals.filter((s) => s.strength === "MODERATE");
  const greenSignals = realSignals.filter((s) => s.strength === "WEAK");
  const totalPosts = realPosts.length;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header
        title={`Signal Dashboard - Project #${projectId || 'Demo'}`}
        subtitle={`Status: ${dashboardStatus.toUpperCase()} · Updated just now`}
      />
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {/* ── Stat cards ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Red Signals"
            value={redSignals.length}
            icon={AlertTriangle}
            color="#ef4444"
            bg="rgba(239,68,68,0.12)"
            border="rgba(239,68,68,0.18)"
            sub="PRR ≥ 5 · Urgent review"
          />
          <StatCard
            label="Amber Signals"
            value={amberSignals.length}
            icon={TrendingUp}
            color="#f59e0b"
            bg="rgba(245,158,11,0.12)"
            border="rgba(245,158,11,0.18)"
            sub="2 ≤ PRR < 5 · Emerging"
          />
          <StatCard
            label="Green Signals"
            value={greenSignals.length}
            icon={Activity}
            color="#22c55e"
            bg="rgba(34,197,94,0.12)"
            border="rgba(34,197,94,0.18)"
            sub="PRR < 2 · Baseline"
          />
          <StatCard
            label="Posts Analyzed"
            value={totalPosts.toLocaleString()}
            icon={FileText}
            color="#818cf8"
            bg="rgba(99,102,241,0.12)"
            border="rgba(99,102,241,0.18)"
            sub="Today · All sources"
          />
        </div>

        {/* ── Timeline chart + Activity ── */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Chart */}
          <div
            className="lg:col-span-2 rounded-xl p-5"
            style={{
              background: "#0c0c14",
              border: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <div className="flex items-start justify-between mb-5">
              <div>
                <h3
                  style={{
                    fontSize: "14px",
                    fontWeight: 600,
                    color: "rgba(255,255,255,0.82)",
                  }}
                >
                  Signal Timeline
                </h3>
                <p
                  style={{
                    fontSize: "12px",
                    color: "rgba(255,255,255,0.30)",
                    marginTop: "2px",
                  }}
                >
                  Drug–symptom pairs · 7-day window
                </p>
              </div>
              <div className="flex gap-1">
                {["7d", "14d", "30d"].map((t, i) => (
                  <button
                    key={t}
                    className="rounded transition-colors"
                    style={{
                      padding: "4px 10px",
                      fontSize: "11px",
                      fontWeight: 500,
                      background:
                        i === 0
                          ? "rgba(255,255,255,0.10)"
                          : "transparent",
                      color:
                        i === 0
                          ? "rgba(255,255,255,0.80)"
                          : "rgba(255,255,255,0.35)",
                    }}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </div>
            {/* Custom legend outside chart to avoid Recharts internal key collisions */}
            <div className="flex flex-wrap gap-3 mb-3">
              {[
                { key: "ibuprofen", color: "#ef4444" },
                { key: "sertraline", color: "#f59e0b" },
                { key: "metformin", color: "#818cf8" },
                { key: "atorvastatin", color: "#22c55e" },
              ].map((item) => (
                <div key={item.key} className="flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full"
                    style={{ background: item.color }}
                  />
                  <span style={{ fontSize: 11, color: "rgba(255,255,255,0.45)" }}>
                    {item.key}
                  </span>
                </div>
              ))}
            </div>
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timelineData}>
                <CartesianGrid
                  key="grid"
                  strokeDasharray="3 3"
                  stroke="rgba(255,255,255,0.045)"
                />
                <XAxis
                  key="x-axis"
                  dataKey="date"
                  tick={{ fill: "rgba(255,255,255,0.32)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  key="y-axis"
                  tick={{ fill: "rgba(255,255,255,0.32)", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={28}
                />
                <Tooltip key="tooltip" content={<CustomTooltip />} />
                <Line
                  key="line-ibuprofen"
                  type="monotone"
                  dataKey="ibuprofen"
                  name="ibuprofen"
                  stroke="#ef4444"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
                <Line
                  key="line-sertraline"
                  type="monotone"
                  dataKey="sertraline"
                  name="sertraline"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
                <Line
                  key="line-metformin"
                  type="monotone"
                  dataKey="metformin"
                  name="metformin"
                  stroke="#818cf8"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
                <Line
                  key="line-atorvastatin"
                  type="monotone"
                  dataKey="atorvastatin"
                  name="atorvastatin"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {/* Activity Feed */}
          <div
            className="rounded-xl p-5 flex flex-col"
            style={{
              background: "#0c0c14",
              border: "1px solid rgba(255,255,255,0.06)",
            }}
          >
            <h3
              className="mb-4"
              style={{
                fontSize: "14px",
                fontWeight: 600,
                color: "rgba(255,255,255,0.82)",
              }}
            >
              Recent Activity
            </h3>
            <div className="space-y-1.5 flex-1 overflow-y-auto">
              {realPosts.length === 0 && <p className="text-white/30 text-xs text-center py-4">Posts will appear as they are processed...</p>}
              {realPosts.map((post, idx) => {
                const dotColor = post.ae_flag ? "#ef4444" : "#22c55e";
                return (
                  <div
                    key={idx}
                    className="flex gap-3 p-2.5 rounded-lg cursor-pointer transition-colors hover:bg-white/[0.03]"
                  >
                    <div
                      className="mt-1 w-1.5 h-1.5 rounded-full shrink-0"
                      style={{ background: dotColor, marginTop: "5px" }}
                    />
                    <div className="min-w-0">
                      <p
                        className="leading-snug line-clamp-3"
                        style={{
                          fontSize: "12px",
                          color: "rgba(255,255,255,0.55)",
                        }}
                      >
                        {post.text}
                      </p>
                      <p
                        className="mt-1"
                        style={{
                          fontSize: "10px",
                          color: "rgba(255,255,255,0.25)",
                        }}
                      >
                        {post.platform} • {post.sentiment} {post.ae_flag && "• AE Flagged"}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── Top Drugs Table ── */}
        <div
          className="rounded-xl overflow-hidden"
          style={{
            background: "#0c0c14",
            border: "1px solid rgba(255,255,255,0.06)",
          }}
        >
          <div
            className="flex items-center justify-between px-6 py-4"
            style={{ borderBottom: "1px solid rgba(255,255,255,0.055)" }}
          >
            <div>
              <h3
                style={{
                  fontSize: "14px",
                  fontWeight: 600,
                  color: "rgba(255,255,255,0.82)",
                }}
              >
                Top Drugs at Risk
              </h3>
              <p
                style={{
                  fontSize: "12px",
                  color: "rgba(255,255,255,0.28)",
                  marginTop: "2px",
                }}
              >
                Sorted by PRR · All active signals
              </p>
            </div>
            <button
              onClick={() => navigate("/worklist")}
              className="flex items-center gap-1.5 transition-colors"
              style={{
                fontSize: "12px",
                fontWeight: 500,
                color: "rgba(129,140,248,0.7)",
              }}
              onMouseEnter={(e) =>
                ((e.currentTarget as HTMLElement).style.color = "#818cf8")
              }
              onMouseLeave={(e) =>
                ((e.currentTarget as HTMLElement).style.color =
                  "rgba(129,140,248,0.7)")
              }
            >
              View worklist{" "}
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.045)" }}>
                  {[
                    "Drug",
                    "Symptom",
                    "Severity",
                    "PRR",
                    "ROR",
                    "Chi²",
                    "Posts",
                    "Status",
                    "Detail",
                  ].map((h) => (
                    <th
                      key={h}
                      className="text-left whitespace-nowrap"
                      style={{
                        padding: "10px 16px",
                        fontSize: "10px",
                        fontWeight: 600,
                        color: "rgba(255,255,255,0.28)",
                        letterSpacing: "0.05em",
                        textTransform: "uppercase",
                      }}
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {realSignals.length === 0 ? (
                  <tr><td colSpan={9} className="text-center py-8 text-white/50"><Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" /> Waiting for signal detection...</td></tr>
                ) : realSignals
                  .map((sig) => (
                    <tr
                      key={sig.id}
                      className="cursor-pointer transition-colors"
                      style={{ borderBottom: "1px solid rgba(255,255,255,0.035)" }}
                      onClick={() => navigate(`/signals/${sig.id}`)}
                      onMouseEnter={(e) =>
                        ((e.currentTarget as HTMLElement).style.background =
                          "rgba(255,255,255,0.018)")
                      }
                      onMouseLeave={(e) =>
                        ((e.currentTarget as HTMLElement).style.background =
                          "transparent")
                      }
                    >
                      <td
                        className="whitespace-nowrap"
                        style={{
                          padding: "12px 16px",
                          fontSize: "13px",
                          fontWeight: 500,
                          color: "rgba(255,255,255,0.80)",
                        }}
                      >
                        {sig.drug}
                      </td>
                      <td
                        className="whitespace-nowrap"
                        style={{
                          padding: "12px 16px",
                          fontSize: "13px",
                          color: "rgba(255,255,255,0.52)",
                        }}
                      >
                        {sig.symptom}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <SeverityBadge severity={sig.strength === "STRONG" ? "RED" : sig.strength === "MODERATE" ? "AMBER" : "GREEN"} size="sm" />
                      </td>
                      <td
                        className="whitespace-nowrap font-mono"
                        style={{
                          padding: "12px 16px",
                          fontSize: "12px",
                          color: "rgba(255,255,255,0.68)",
                        }}
                      >
                        {sig.prr.toFixed(1)}
                      </td>
                      <td
                        className="whitespace-nowrap font-mono"
                        style={{
                          padding: "12px 16px",
                          fontSize: "12px",
                          color: "rgba(255,255,255,0.45)",
                        }}
                      >
                        {sig.ror.toFixed(1)}
                      </td>
                      <td
                        className="whitespace-nowrap font-mono"
                        style={{
                          padding: "12px 16px",
                          fontSize: "12px",
                          color: "rgba(255,255,255,0.45)",
                        }}
                      >
                        {sig.chi2.toFixed(1)}
                      </td>
                      <td
                        className="whitespace-nowrap"
                        style={{
                          padding: "12px 16px",
                          fontSize: "13px",
                          color: "rgba(255,255,255,0.52)",
                        }}
                      >
                        {sig.postCount.toLocaleString()}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <StatusBadge status={sig.status} />
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <button
                          className="flex items-center gap-1 transition-colors"
                          style={{
                            fontSize: "11px",
                            fontWeight: 500,
                            color: "rgba(129,140,248,0.55)",
                          }}
                          onMouseEnter={(e) =>
                            ((e.currentTarget as HTMLElement).style.color =
                              "#818cf8")
                          }
                          onMouseLeave={(e) =>
                            ((e.currentTarget as HTMLElement).style.color =
                              "rgba(129,140,248,0.55)")
                          }
                        >
                          Details{" "}
                          <ArrowUpRight className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}