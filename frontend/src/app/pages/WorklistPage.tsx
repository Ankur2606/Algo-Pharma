import { useState } from "react";
import { useNavigate } from "react-router";
import { Header } from "../components/layout/Header";
import { SeverityBadge } from "../components/shared/SeverityBadge";
import { StatusBadge } from "../components/shared/StatusBadge";
import { signals, type Severity, type SignalStatus } from "../data/mockData";
import {
  Search,
  Filter,
  CheckSquare,
  Download,
  ChevronDown,
  CheckCircle,
  ExternalLink,
} from "lucide-react";

const analysts = ["All Analysts", "Dr. Priya Sharma", "Dr. Amit Verma", "Dr. Rahul Nair", "Unassigned"];

export function WorklistPage() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState<Severity | "ALL">("ALL");
  const [statusFilter, setStatusFilter] = useState<SignalStatus | "ALL">("ALL");
  const [analystFilter, setAnalystFilter] = useState("All Analysts");
  const [selected, setSelected] = useState<string[]>([]);

  const filtered = signals.filter((sig) => {
    const matchSearch =
      sig.drug.toLowerCase().includes(search.toLowerCase()) ||
      sig.symptom.toLowerCase().includes(search.toLowerCase());
    const matchSeverity = severityFilter === "ALL" || sig.severity === severityFilter;
    const matchStatus = statusFilter === "ALL" || sig.status === statusFilter;
    const matchAnalyst = analystFilter === "All Analysts" || sig.analyst === analystFilter;
    return matchSearch && matchSeverity && matchStatus && matchAnalyst;
  });

  const toggleSelect = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selected.length === filtered.length) setSelected([]);
    else setSelected(filtered.map((s) => s.id));
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header
        title="Signal Triage Worklist"
        subtitle={`${filtered.length} signals · ${selected.length} selected`}
        actions={
          selected.length > 0 ? (
            <div className="flex items-center gap-2">
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition-colors">
                <CheckCircle className="w-3.5 h-3.5" /> Confirm All
              </button>
              <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-white/[0.06] hover:bg-white/[0.10] text-white/70 border border-white/[0.08] transition-colors">
                <Download className="w-3.5 h-3.5" /> Export All
              </button>
            </div>
          ) : undefined
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {/* Search */}
          <div className="relative flex-1 min-w-52">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search drug or symptom..."
              className="w-full pl-9 pr-4 py-2 rounded-lg text-sm placeholder:text-white/25 focus:outline-none focus:border-indigo-500/40 transition-colors"
              style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.70)", fontSize: "13px" }}
              onFocus={e => (e.currentTarget as HTMLElement).style.borderColor = "rgba(99,102,241,0.45)"}
              onBlur={e => (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.08)"}
            />
          </div>

          {/* Severity filter */}
          <div className="relative">
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value as any)}
              className="appearance-none rounded-lg pl-3 pr-8 py-2 text-sm focus:outline-none cursor-pointer"
              style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.55)", fontSize: "13px" }}
            >
              <option value="ALL">All Severities</option>
              <option value="RED">Red</option>
              <option value="AMBER">Amber</option>
              <option value="GREEN">Green</option>
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
          </div>

          {/* Status filter */}
          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as any)}
              className="appearance-none rounded-lg pl-3 pr-8 py-2 text-sm focus:outline-none cursor-pointer"
              style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.55)", fontSize: "13px" }}
            >
              <option value="ALL">All Statuses</option>
              <option value="NEW">New</option>
              <option value="IN_REVIEW">In Review</option>
              <option value="CONFIRMED">Confirmed</option>
              <option value="EXPORTED">Exported</option>
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
          </div>

          {/* Analyst filter */}
          <div className="relative">
            <select
              value={analystFilter}
              onChange={(e) => setAnalystFilter(e.target.value)}
              className="appearance-none rounded-lg pl-3 pr-8 py-2 text-sm focus:outline-none cursor-pointer"
              style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.55)", fontSize: "13px" }}
            >
              {analysts.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
          </div>

          <button className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors" style={{ color: "rgba(255,255,255,0.45)", background: "#0c0c14", border: "1px solid rgba(255,255,255,0.08)", fontSize: "13px" }}>
            <Filter className="w-3.5 h-3.5" /> More Filters
          </button>
        </div>

        {/* Table */}
        <div className="rounded-xl overflow-hidden" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.045)" }}>
                  <th className="px-4 py-3 text-left">
                    <button onClick={toggleAll}>
                      <CheckSquare
                        className={`w-4 h-4 ${
                          selected.length > 0 ? "text-indigo-400" : "text-white/20"
                        }`}
                      />
                    </button>
                  </th>
                  {["Drug", "Symptom", "Severity", "Posts", "PRR", "Last Updated", "Analyst", "Status", "Action"].map(
                    (h) => (
                      <th
                        key={h}
                        className="text-left whitespace-nowrap"
                        style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="text-center py-12" style={{ fontSize: "14px", color: "rgba(255,255,255,0.28)" }}>
                      No signals match your filters.
                    </td>
                  </tr>
                ) : (
                  filtered.map((sig) => (
                    <tr
                      key={sig.id}
                      className="transition-colors"
                      style={{ borderBottom: "1px solid rgba(255,255,255,0.035)", background: selected.includes(sig.id) ? "rgba(99,102,241,0.05)" : "transparent" }}
                      onMouseEnter={e => { if (!selected.includes(sig.id)) (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.018)" }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = selected.includes(sig.id) ? "rgba(99,102,241,0.05)" : "transparent" }}
                    >
                      <td className="px-4 py-3">
                        <button onClick={() => toggleSelect(sig.id)}>
                          <CheckSquare
                            className={`w-4 h-4 ${
                              selected.includes(sig.id)
                                ? "text-indigo-400"
                                : "text-white/20 hover:text-white/40"
                            }`}
                          />
                        </button>
                      </td>
                      <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.80)" }}>
                        {sig.drug}
                      </td>
                      <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", color: "rgba(255,255,255,0.52)" }}>
                        {sig.symptom}
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <SeverityBadge severity={sig.severity} size="sm" />
                      </td>
                      <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", color: "rgba(255,255,255,0.52)" }}>
                        {sig.postCount.toLocaleString()}
                      </td>
                      <td className="whitespace-nowrap font-mono" style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.52)" }}>
                        {sig.prr.toFixed(1)}
                      </td>
                      <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.35)" }}>
                        {new Date(sig.lastUpdated).toLocaleDateString("en-IN", {
                          day: "numeric",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </td>
                      <td className="whitespace-nowrap" style={{ padding: "12px 16px" }}>
                        <div className="relative">
                          <select
                            defaultValue={sig.analyst}
                            className="appearance-none bg-transparent pr-4 focus:outline-none cursor-pointer"
                            style={{ fontSize: "12px", color: "rgba(255,255,255,0.45)" }}
                            onClick={(e) => e.stopPropagation()}
                          >
                            {analysts.slice(1).map((a) => (
                              <option key={a} value={a}>
                                {a}
                              </option>
                            ))}
                          </select>
                          <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-3 h-3 text-white/20 pointer-events-none" />
                        </div>
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <StatusBadge status={sig.status} />
                      </td>
                      <td style={{ padding: "12px 16px" }}>
                        <button
                          onClick={() => navigate(`/signals/${sig.id}`)}
                          className="flex items-center gap-1 transition-colors"
                          style={{ fontSize: "12px", fontWeight: 500, color: "rgba(129,140,248,0.55)" }}
                          onMouseEnter={e => (e.currentTarget as HTMLElement).style.color = "#818cf8"}
                          onMouseLeave={e => (e.currentTarget as HTMLElement).style.color = "rgba(129,140,248,0.55)"}
                        >
                          View <ExternalLink className="w-3 h-3" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between px-5 py-3" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)" }}>
              Showing {filtered.length} of {signals.length} signals
            </p>
            <div className="flex gap-1">
              {[1, 2, 3].map((p) => (
                <button
                  key={p}
                  className="w-7 h-7 rounded text-xs transition-colors"
                  style={p === 1 ? { background: "rgba(99,102,241,0.2)", color: "#818cf8" } : { color: "rgba(255,255,255,0.30)" }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}