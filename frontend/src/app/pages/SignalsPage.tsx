import { useNavigate } from "react-router";
import { Header } from "../components/layout/Header";
import { SeverityBadge } from "../components/shared/SeverityBadge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { signals } from "../data/mockData";
import { ExternalLink, TrendingUp, ArrowUp, ArrowDown } from "lucide-react";
import { useState } from "react";

type SortKey = "prr" | "ror" | "chi2" | "postCount" | "confidence";

export function SignalsPage() {
  const navigate = useNavigate();
  const [sortKey, setSortKey] = useState<SortKey>("prr");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sorted = [...signals].sort((a, b) => {
    const v = sortDir === "desc" ? b[sortKey] - a[sortKey] : a[sortKey] - b[sortKey];
    return v;
  });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(sortDir === "desc" ? "asc" : "desc");
    else { setSortKey(key); setSortDir("desc"); }
  };

  const SortIcon = ({ k }: { k: SortKey }) =>
    sortKey === k ? (
      sortDir === "desc" ? <ArrowDown className="w-3 h-3" /> : <ArrowUp className="w-3 h-3" />
    ) : null;

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header
        title="All Signals"
        subtitle={`${signals.length} signals detected · ${signals.filter(s => s.severity === "RED").length} urgent`}
      />
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {/* Severity summary */}
        <div className="flex flex-wrap gap-3 mb-5">
          {[
            { label: "Red (Urgent)", count: signals.filter(s => s.severity === "RED").length, color: "#ef4444", dot: "#ef4444" },
            { label: "Amber (Emerging)", count: signals.filter(s => s.severity === "AMBER").length, color: "#f59e0b", dot: "#f59e0b" },
            { label: "Green (Baseline)", count: signals.filter(s => s.severity === "GREEN").length, color: "#22c55e", dot: "#22c55e" },
          ].map(({ label, count, color, dot }) => (
            <div key={label} className="flex items-center gap-2.5 px-4 py-2 rounded-lg" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.07)" }}>
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: dot }} />
              <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.40)" }}>{label}:</span>
              <span style={{ fontSize: "13px", fontWeight: 600, color }}>{count}</span>
            </div>
          ))}
          <div className="flex items-center gap-2.5 px-4 py-2 rounded-lg ml-auto" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.07)" }}>
            <TrendingUp className="w-3.5 h-3.5" style={{ color: "#818cf8" }} />
            <span style={{ fontSize: "12px", color: "rgba(255,255,255,0.40)" }}>Avg PRR:</span>
            <span style={{ fontSize: "13px", fontWeight: 600, color: "#818cf8" }}>
              {(signals.reduce((a, b) => a + b.prr, 0) / signals.length).toFixed(1)}
            </span>
          </div>
        </div>

        <div className="rounded-xl overflow-hidden" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.045)" }}>
                  <th className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Drug</th>
                  <th className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Symptom</th>
                  <th className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Severity</th>
                  {([["prr", "PRR"], ["ror", "ROR"], ["chi2", "Chi²"], ["postCount", "Posts"], ["confidence", "Conf %"]] as [SortKey, string][]).map(([k, label]) => (
                    <th
                      key={k}
                      className="text-left whitespace-nowrap cursor-pointer"
                      style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: sortKey === k ? "#818cf8" : "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}
                      onClick={() => toggleSort(k)}
                    >
                      <span className="flex items-center gap-1">
                        {label}
                        <SortIcon k={k} />
                      </span>
                    </th>
                  ))}
                  <th className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Status</th>
                  <th className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Source</th>
                  <th style={{ padding: "10px 16px" }}></th>
                </tr>
              </thead>
              <tbody>
                {sorted.map((sig) => (
                  <tr
                    key={sig.id}
                    className="cursor-pointer transition-colors"
                    style={{ borderBottom: "1px solid rgba(255,255,255,0.035)" }}
                    onClick={() => navigate(`/signals/${sig.id}`)}
                    onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.018)"}
                    onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                  >
                    <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.80)" }}>
                      {sig.drug}
                    </td>
                    <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", color: "rgba(255,255,255,0.52)" }}>{sig.symptom}</td>
                    <td style={{ padding: "12px 16px" }}>
                      <SeverityBadge severity={sig.severity} size="sm" />
                    </td>
                    <td className="font-mono" style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.68)" }}>{sig.prr.toFixed(2)}</td>
                    <td className="font-mono" style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>{sig.ror.toFixed(2)}</td>
                    <td className="font-mono" style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>{sig.chi2.toFixed(1)}</td>
                    <td style={{ padding: "12px 16px", fontSize: "13px", color: "rgba(255,255,255,0.52)" }}>{sig.postCount.toLocaleString()}</td>
                    <td style={{ padding: "12px 16px" }}>
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1" style={{ background: "rgba(255,255,255,0.07)", borderRadius: "2px", overflow: "hidden" }}>
                          <div className="h-full rounded" style={{ width: `${sig.confidence}%`, background: "#818cf8" }} />
                        </div>
                        <span className="font-mono" style={{ fontSize: "11px", color: "rgba(255,255,255,0.45)" }}>{sig.confidence}%</span>
                      </div>
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <StatusBadge status={sig.status} />
                    </td>
                    <td style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.35)" }}>
                      {sig.source}
                    </td>
                    <td style={{ padding: "12px 16px" }}>
                      <button className="transition-colors" style={{ color: "rgba(129,140,248,0.55)" }}
                        onMouseEnter={e => (e.currentTarget as HTMLElement).style.color = "#818cf8"}
                        onMouseLeave={e => (e.currentTarget as HTMLElement).style.color = "rgba(129,140,248,0.55)"}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
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