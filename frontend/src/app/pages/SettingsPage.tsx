import { useState } from "react";
import { Header } from "../components/layout/Header";
import { crawlerJobs } from "../data/mockData";
import {
  Plus,
  Play,
  Pause,
  Trash2,
  Globe,
  ChevronDown,
  Toggle,
  CheckCircle,
  Twitter,
  FileText,
} from "lucide-react";

const piiCategories = [
  { id: "aadhaar", label: "Aadhaar Number", enabled: true },
  { id: "pan", label: "PAN Card", enabled: true },
  { id: "phone", label: "Phone Number", enabled: true },
  { id: "email", label: "Email Address", enabled: true },
  { id: "name", label: "Full Name", enabled: false },
  { id: "dob", label: "Date of Birth", enabled: false },
  { id: "address", label: "Physical Address", enabled: true },
];

const statusConfig: Record<string, { bg: string; text: string; border: string }> = {
  ACTIVE: { bg: "bg-green-500/10", text: "text-green-400", border: "border-green-500/20" },
  PAUSED: { bg: "bg-amber-400/10", text: "text-amber-400", border: "border-amber-400/20" },
  COMPLETED: { bg: "bg-white/5", text: "text-white/40", border: "border-white/10" },
  FAILED: { bg: "bg-red-500/10", text: "text-red-400", border: "border-red-500/20" },
};

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<"crawlers" | "redaction" | "export">("crawlers");
  const [pii, setPii] = useState(piiCategories);
  const [testInput, setTestInput] = useState(
    "Patient John Doe (DOB: 12-05-1985) reported issues. Call 9812345678 or email john.doe@gmail.com. Aadhaar: 1234 5678 9012"
  );
  const [testOutput, setTestOutput] = useState("");
  const [showAddCrawler, setShowAddCrawler] = useState(false);

  const handleRedact = () => {
    let result = testInput;
    if (pii.find((p) => p.id === "phone" && p.enabled))
      result = result.replace(/\b\d{10}\b/g, "[PHONE]");
    if (pii.find((p) => p.id === "email" && p.enabled))
      result = result.replace(/\S+@\S+\.\S+/g, "[EMAIL]");
    if (pii.find((p) => p.id === "aadhaar" && p.enabled))
      result = result.replace(/\d{4}\s\d{4}\s\d{4}/g, "[AADHAAR]");
    if (pii.find((p) => p.id === "dob" && p.enabled))
      result = result.replace(/\d{2}-\d{2}-\d{4}/g, "[DOB]");
    if (pii.find((p) => p.id === "name" && p.enabled))
      result = result.replace(/John Doe/g, "[NAME]");
    setTestOutput(result);
  };

  const togglePii = (id: string) => {
    setPii((prev) =>
      prev.map((p) => (p.id === id ? { ...p, enabled: !p.enabled } : p))
    );
  };

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <Header title="Configuration & Settings" subtitle="Admin panel · AlgoPharma" />

      <div className="flex-1 overflow-y-auto px-6 py-5">
        {/* Tabs */}
        <div className="flex gap-1 mb-5 rounded-xl p-1 w-fit" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.07)" }}>
          {(["crawlers", "redaction", "export"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-1.5 rounded-lg text-sm capitalize transition-colors ${
                activeTab === tab
                  ? "bg-white/10 text-white/80"
                  : "text-white/40 hover:text-white/60"
              }`}
            >
              {tab === "crawlers" ? "Crawler Jobs" : tab === "redaction" ? "PII Redaction" : "Export Settings"}
            </button>
          ))}
        </div>

        {/* Crawlers Tab */}
        {activeTab === "crawlers" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)" }}>
                  Active Crawl Jobs
                </h3>
                <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginTop: "2px" }}>
                  {crawlerJobs.filter((j) => j.status === "ACTIVE").length} of {crawlerJobs.length} crawlers running
                </p>
              </div>
              <button
                onClick={() => setShowAddCrawler(!showAddCrawler)}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white transition-colors"
                style={{ background: "#6366f1", fontSize: "13px" }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#4f46e5"}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#6366f1"}
              >
                <Plus className="w-4 h-4" /> Add Crawler
              </button>
            </div>

            {/* Add Crawler Form */}
            {showAddCrawler && (
              <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(99,102,241,0.25)" }}>
                <h4 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.70)", marginBottom: "16px" }}>
                  New Crawl Job
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[
                    { label: "Source URL / Subreddit", placeholder: "r/medicine or @hashtag", type: "text" },
                    { label: "Keyword(s)", placeholder: "e.g. adverse drug reaction", type: "text" },
                    { label: "Language", placeholder: "en", type: "text" },
                  ].map(({ label, placeholder, type }) => (
                    <div key={label}>
                      <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                        {label}
                      </label>
                      <input
                        type={type}
                        placeholder={placeholder}
                        className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2 text-white/70 text-sm placeholder:text-white/20 focus:outline-none focus:border-indigo-500/40"
                      />
                    </div>
                  ))}
                  <div>
                    <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                      Frequency
                    </label>
                    <div className="relative">
                      <select className="w-full appearance-none bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 pr-8 py-2 text-white/70 text-sm focus:outline-none focus:border-indigo-500/40">
                        <option>Hourly</option>
                        <option>Daily</option>
                        <option>Weekly</option>
                      </select>
                      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
                    </div>
                  </div>
                  <div>
                    <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                      Source Type
                    </label>
                    <div className="relative">
                      <select className="w-full appearance-none bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 pr-8 py-2 text-white/70 text-sm focus:outline-none focus:border-indigo-500/40">
                        <option>Reddit</option>
                        <option>Twitter/X</option>
                        <option>Forum URL</option>
                      </select>
                      <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => setShowAddCrawler(false)}
                    className="px-4 py-2 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                  >
                    Start Crawler
                  </button>
                  <button
                    onClick={() => setShowAddCrawler(false)}
                    className="px-4 py-2 rounded-lg text-sm text-white/40 hover:text-white/60 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            {/* Crawler Table */}
            <div className="rounded-xl overflow-hidden" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr style={{ borderBottom: "1px solid rgba(255,255,255,0.045)" }}>
                      {["Source", "Type", "Keyword", "Frequency", "Status", "Posts", "Last Run", ""].map((h) => (
                        <th key={h} className="text-left whitespace-nowrap" style={{ padding: "10px 16px", fontSize: "10px", fontWeight: 600, color: "rgba(255,255,255,0.28)", letterSpacing: "0.05em", textTransform: "uppercase" }}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {crawlerJobs.map((job) => {
                      const sc = statusConfig[job.status];
                      return (
                        <tr key={job.id} className="transition-colors" style={{ borderBottom: "1px solid rgba(255,255,255,0.035)" }}
                          onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.018)"}
                          onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                        >
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.80)" }}>
                            {job.source}
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.80)" }}>
                            <span className="flex items-center gap-1.5 text-white/50" style={{ fontSize: "12px" }}>
                              {job.type === "reddit" ? (
                                <Globe className="w-3.5 h-3.5 text-orange-400" />
                              ) : job.type === "twitter" ? (
                                <Twitter className="w-3.5 h-3.5 text-sky-400" />
                              ) : (
                                <FileText className="w-3.5 h-3.5 text-white/30" />
                              )}
                              {job.type}
                            </span>
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.50)" }}>
                            {job.keyword}
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.50)" }}>
                            {job.frequency}
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.50)" }}>
                            <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[10px] font-medium ${sc.bg} ${sc.text} ${sc.border}`}>
                              {job.status === "ACTIVE" && <span className="w-1.5 h-1.5 rounded-full bg-green-500" />}
                              {job.status}
                            </span>
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.50)" }}>
                            {job.postsCollected.toLocaleString()}
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.40)" }}>
                            {new Date(job.lastRun).toLocaleDateString("en-IN", {
                              day: "numeric",
                              month: "short",
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                          <td className="whitespace-nowrap" style={{ padding: "12px 16px", fontSize: "13px", fontWeight: 500, color: "rgba(255,255,255,0.50)" }}>
                            <div className="flex items-center gap-1.5">
                              <button className="w-7 h-7 flex items-center justify-center rounded text-white/30 hover:text-white/60 hover:bg-white/[0.04] transition-colors">
                                {job.status === "ACTIVE" ? (
                                  <Pause className="w-3.5 h-3.5" />
                                ) : (
                                  <Play className="w-3.5 h-3.5" />
                                )}
                              </button>
                              <button className="w-7 h-7 flex items-center justify-center rounded text-white/30 hover:text-red-400 hover:bg-red-500/5 transition-colors">
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* PII Redaction Tab */}
        {activeTab === "redaction" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
                PII Categories
              </h3>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
                Toggle which PII types to redact from posts
              </p>
              <div className="space-y-3">
                {pii.map((item) => (
                  <div key={item.id} className="flex items-center justify-between py-2 border-b border-white/[0.04]">
                    <div>
                      <p className="text-white/70" style={{ fontSize: "13px" }}>{item.label}</p>
                      <p className="text-white/30" style={{ fontSize: "11px" }}>
                        Masked as [{item.id.toUpperCase()}]
                      </p>
                    </div>
                    <button
                      onClick={() => togglePii(item.id)}
                      className={`relative w-10 h-5 rounded-full transition-colors ${
                        item.enabled ? "bg-indigo-600" : "bg-white/10"
                      }`}
                    >
                      <span
                        className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm ${
                          item.enabled ? "translate-x-5" : "translate-x-0.5"
                        }`}
                      />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
                Test Redaction
              </h3>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
                Paste text to preview the redacted version
              </p>
              <div className="space-y-3">
                <div>
                  <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                    Input text
                  </label>
                  <textarea
                    value={testInput}
                    onChange={(e) => setTestInput(e.target.value)}
                    rows={5}
                    className="w-full bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-2.5 text-white/60 text-sm placeholder:text-white/20 focus:outline-none focus:border-indigo-500/40 resize-none"
                  />
                </div>
                <button
                  onClick={handleRedact}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                >
                  <CheckCircle className="w-4 h-4" /> Run Redaction
                </button>
                {testOutput && (
                  <div>
                    <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                      Redacted output
                    </label>
                    <div className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2.5 text-white/60 text-sm leading-relaxed">
                      {testOutput}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Export Tab */}
        {activeTab === "export" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="rounded-xl p-5 space-y-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <div>
                <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
                  Export Settings
                </h3>
                <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)" }}>
                  Configure PvPI export defaults
                </p>
              </div>
              {[
                {
                  label: "Default Regulatory Body",
                  options: ["VigiFlow (WHO)", "NCLT", "CDSCO Direct", "Custom"],
                  default: "VigiFlow (WHO)",
                },
                {
                  label: "Export Format",
                  options: ["PvPI CSV", "E2B(R3) XML", "MedDRA Coded", "JSON"],
                  default: "PvPI CSV",
                },
                {
                  label: "Batch Export Schedule",
                  options: ["Manual only", "Daily at 9:00 AM", "Weekly Monday", "Monthly 1st"],
                  default: "Manual only",
                },
              ].map(({ label, options, default: def }) => (
                <div key={label}>
                  <label className="block text-white/40 mb-1.5" style={{ fontSize: "12px" }}>
                    {label}
                  </label>
                  <div className="relative">
                    <select
                      defaultValue={def}
                      className="w-full appearance-none bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 pr-8 py-2.5 text-white/70 text-sm focus:outline-none focus:border-indigo-500/40"
                    >
                      {options.map((o) => (
                        <option key={o} value={o}>
                          {o}
                        </option>
                      ))}
                    </select>
                    <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30 pointer-events-none" />
                  </div>
                </div>
              ))}
              <button className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm text-white transition-colors" style={{ background: "#6366f1", fontSize: "13px" }}
                onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "#4f46e5"}
                onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "#6366f1"}
              >
                <CheckCircle className="w-4 h-4" /> Save Settings
              </button>
            </div>

            <div className="rounded-xl p-5" style={{ background: "#0c0c14", border: "1px solid rgba(255,255,255,0.06)" }}>
              <h3 style={{ fontSize: "14px", fontWeight: 600, color: "rgba(255,255,255,0.82)", marginBottom: "4px" }}>
                System Information
              </h3>
              <p style={{ fontSize: "12px", color: "rgba(255,255,255,0.28)", marginBottom: "16px" }}>
                Platform metadata and compliance
              </p>
              <div className="space-y-3">
                {[
                  { label: "Platform Version", value: "AlgoPharma v1.0.0" },
                  { label: "Compliance", value: "CDSCO · PvPI · ICH E2B(R3)" },
                  { label: "NLP Model", value: "BioMedBERT v2.3" },
                  { label: "PII Framework", value: "Presidio (Microsoft)" },
                  { label: "Signal Algorithm", value: "PRR / ROR / Chi²" },
                  { label: "Data Retention", value: "90 days rolling window" },
                  { label: "Last Backup", value: "2026-05-04 · 03:00 IST" },
                ].map(({ label, value }) => (
                  <div key={label} className="flex justify-between py-2 border-b border-white/[0.04]">
                    <span className="text-white/40" style={{ fontSize: "12px" }}>{label}</span>
                    <span className="text-white/60" style={{ fontSize: "12px" }}>{value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}