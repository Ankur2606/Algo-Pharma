import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { Header } from "../components/layout/Header";

const topDrugData = [
  { drug: "Sertraline", signals: 12, red: 4, amber: 5, green: 3 },
  { drug: "Ibuprofen", signals: 10, red: 3, amber: 4, green: 3 },
  { drug: "Metformin", signals: 9, red: 3, amber: 3, green: 3 },
  { drug: "Atorvastatin", signals: 7, red: 1, amber: 4, green: 2 },
  { drug: "Amlodipine", signals: 6, red: 1, amber: 3, green: 2 },
  { drug: "Lisinopril", signals: 5, red: 0, amber: 2, green: 3 },
  { drug: "Pantoprazole", signals: 4, red: 0, amber: 2, green: 2 },
  { drug: "Cetirizine", signals: 3, red: 0, amber: 1, green: 2 },
];

const topSymptomData = [
  { symptom: "GI Bleeding", count: 52 },
  { symptom: "Suicidal Ideation", count: 41 },
  { symptom: "Lactic Acidosis", count: 38 },
  { symptom: "Myopathy", count: 29 },
  { symptom: "Peripheral Edema", count: 24 },
  { symptom: "Dry Cough", count: 18 },
  { symptom: "Drowsiness", count: 15 },
  { symptom: "Hypomagnesemia", count: 12 },
];

const sourceData = [
  { name: "Reddit", value: 48, color: "#818cf8" },
  { name: "Twitter", value: 35, color: "#6366f1" },
  { name: "MedForum", value: 17, color: "#4f46e5" },
];

const statusData = [
  { name: "New", value: 3, color: "#60a5fa" },
  { name: "In Review", value: 2, color: "#a78bfa" },
  { name: "Confirmed", value: 2, color: "#34d399" },
  { name: "Exported", value: 1, color: "#6b7280" },
];

const exportHistory = [
  {
    id: 1,
    signal: "Lisinopril → Dry Cough",
    body: "VigiFlow",
    date: "2026-05-01",
    analyst: "Dr. Amit Verma",
    format: "PvPI CSV",
  },
  {
    id: 2,
    signal: "Cetirizine → Drowsiness",
    body: "NCLT",
    date: "2026-04-28",
    analyst: "Dr. Rahul Nair",
    format: "PvPI CSV",
  },
  {
    id: 3,
    signal: "Amlodipine → Peripheral Edema",
    body: "VigiFlow",
    date: "2026-04-22",
    analyst: "Dr. Priya Sharma",
    format: "PvPI CSV",
  },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#1a1a2e] border border-white/10 rounded-lg p-3 text-xs shadow-xl">
        <p className="text-white/60 mb-1">{label}</p>
        {payload.map((p: any, i: number) => (
          <div key={p.dataKey || p.name || `tooltip-item-${i}`} className="flex items-center gap-2 py-0.5">
            <span className="w-2 h-2 rounded-full" style={{ background: p.fill || p.color }} />
            <span className="text-white/70">{p.name}:</span>
            <span className="text-white/90 font-medium">{p.value}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function AnalyticsPage() {
  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header
        title="Analytics & Reporting"
        subtitle="30-day signal trend overview"
      />
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-5">
        {/* Summary stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Total Signals (30d)", value: "56", change: "+12%", up: true },
            { label: "Confirmed Signals", value: "18", change: "+5%", up: true },
            { label: "Posts Analyzed", value: "74,132", change: "+31%", up: true },
            { label: "Exports Generated", value: "3", change: "-2", up: false },
          ].map(({ label, value, change, up }) => (
            <div key={label} className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <p style={{ fontSize: "12px", fontWeight: 500, color: "rgba(255,255,255,0.38)" }}>{label}</p>
              <p style={{ fontSize: "28px", fontWeight: 700, color: "rgba(255,255,255,0.88)", lineHeight: 1.1, letterSpacing: "-0.02em", marginTop: "6px", marginBottom: "4px" }}>
                {value}
              </p>
              <p style={{ fontSize: "11px", color: up ? "#22c55e" : "#ef4444" }}>
                {change} vs last month
              </p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Top Drugs by Signal Count */}
          <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Top Drugs by Signal Count
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              30-day window · by severity
            </p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height={224}>
                <BarChart data={topDrugData} layout="vertical" barSize={10}>
                  <CartesianGrid key="grid" strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                  <XAxis key="x-axis" type="number" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis key="y-axis" type="category" dataKey="drug" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} width={72} />
                  <Tooltip key="tooltip" content={<CustomTooltip />} />
                  <Bar key="bar-red" dataKey="red" name="Red" stackId="a" fill="#ef4444" radius={[0, 0, 0, 0]} />
                  <Bar key="bar-amber" dataKey="amber" name="Amber" stackId="a" fill="#f59e0b" />
                  <Bar key="bar-green" dataKey="green" name="Green" stackId="a" fill="#22c55e" radius={[0, 2, 2, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Symptoms */}
          <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Top Reported Symptoms
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              By confirmed post count
            </p>
            <div className="h-56">
              <ResponsiveContainer width="100%" height={224}>
                <BarChart data={topSymptomData} layout="vertical" barSize={10}>
                  <CartesianGrid key="grid" strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" horizontal={false} />
                  <XAxis key="x-axis" type="number" tick={{ fill: "rgba(255,255,255,0.35)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis key="y-axis" type="category" dataKey="symptom" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 11 }} axisLine={false} tickLine={false} width={100} />
                  <Tooltip key="tooltip" content={<CustomTooltip />} />
                  <Bar key="bar-count" dataKey="count" name="Posts" fill="#818cf8" radius={[0, 2, 2, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Source Breakdown */}
          <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Source Distribution
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              Posts by platform
            </p>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  key="pie-source"
                  data={sourceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {sourceData.map((entry, index) => (
                    <Cell key={`source-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  key="tooltip"
                  contentStyle={{
                    background: "#1a1a2e",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Custom legend */}
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {sourceData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
                  <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }}>{entry.name}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Status Breakdown */}
          <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
              Signal Status Breakdown
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
              Current pipeline status
            </p>
            <ResponsiveContainer width="100%" height={160}>
              <PieChart>
                <Pie
                  key="pie-status"
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`status-cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  key="tooltip"
                  contentStyle={{
                    background: "#1a1a2e",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "rgba(255,255,255,0.7)",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            {/* Custom legend */}
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {statusData.map((entry) => (
                <div key={entry.name} className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full" style={{ background: entry.color }} />
                  <span style={{ fontSize: 11, color: "rgba(255,255,255,0.5)" }}>{entry.name}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Export History */}
        <div className="rounded-xl overflow-hidden" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
          <div className="px-6 py-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.055)" }}>
            <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)" }}>
              Export History
            </h3>
            <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginTop: "2px" }}>
              Audit trail of all regulatory exports
            </p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.045)" }}>
                {["Signal", "Regulatory Body", "Export Date", "Analyst", "Format"].map((h) => (
                  <th
                    key={h}
                    className="text-left"
                    style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {exportHistory.map((row) => (
                <tr key={row.id} className="transition-colors" style={{ borderBottom: "1px solid rgba(255,255,255,0.035)" }}
                  onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.018)"}
                  onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                >
                  <td style={{ padding: "12px 16px", fontSize: "13px", color: "rgba(255,255,255,0.68)" }}>{row.signal}</td>
                  <td style={{ padding: "12px 16px" }}>
                    <span style={{ fontSize: "11px", fontWeight: 500, padding: "3px 8px", borderRadius: "4px", background: "rgba(99,102,241,0.12)", color: "#818cf8", border: "1px solid rgba(99,102,241,0.22)" }}>
                      {row.body}
                    </span>
                  </td>
                  <td style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>{row.date}</td>
                  <td style={{ padding: "12px 16px", fontSize: "12px", color: "rgba(255,255,255,0.45)" }}>{row.analyst}</td>
                  <td className="font-mono" style={{ padding: "12px 16px", fontSize: "11px", color: "rgba(255,255,255,0.35)" }}>
                    {row.format}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}