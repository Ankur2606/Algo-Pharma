import React, { useEffect, useState, useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router';
import { motion, AnimatePresence } from 'motion/react';
import {
  Activity, AlertTriangle, CheckCircle2, Clock,
  Database, ShieldAlert, FileText, ArrowRight, XCircle,
  ChevronDown, Pill, Globe, Zap, Calendar, CalendarDays, RefreshCw
} from 'lucide-react';
import {
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend
} from 'recharts';
import { useAlgoPharmaAPI, DashboardData } from '../hooks/useAlgoPharmaAPI';

const COLORS = {
  positive: '#10b981',
  neutral: '#64748b',
  negative: '#ef4444',
  ae: '#f59e0b',
  non_ae: '#0d1220',
  bars: ['#6366f1', '#06b6d4', '#f59e0b', '#10b981', '#ef4444']
};

const FREQ_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string; interval: number }> = {
  realtime: { label: 'Real-time', icon: <Zap className="w-3.5 h-3.5" />, color: 'text-cyan-400 bg-cyan-500/15 border-cyan-500/25', interval: 900 },
  daily:    { label: 'Daily',     icon: <Calendar className="w-3.5 h-3.5" />, color: 'text-indigo-400 bg-indigo-500/15 border-indigo-500/25', interval: 86400 },
  weekly:   { label: 'Weekly',    icon: <CalendarDays className="w-3.5 h-3.5" />, color: 'text-violet-400 bg-violet-500/15 border-violet-500/25', interval: 604800 },
};

function fmt(iso: string | null): string {
  if (!iso) return 'N/A';
  return new Date(iso).toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false });
}

function MonitoringCard({
  frequency, lastCrawledAt, nextCrawlAt, crawlHistory
}: {
  frequency: string;
  lastCrawledAt: string | null;
  nextCrawlAt: string | null;
  crawlHistory: any[];
}) {
  const cfg = FREQ_CONFIG[frequency] || { label: frequency, icon: <RefreshCw className="w-3.5 h-3.5" />, color: 'text-slate-400 bg-slate-500/15 border-slate-500/25', interval: 0 };

  // Live countdown to next crawl
  const [countdown, setCountdown] = React.useState('');
  React.useEffect(() => {
    if (!nextCrawlAt) return;
    const tick = () => {
      const diff = Math.max(0, new Date(nextCrawlAt).getTime() - Date.now());
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setCountdown(diff === 0 ? 'crawling now...' : `${h > 0 ? `${h}h ` : ''}${m}m ${s}s`);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [nextCrawlAt]);

  return (
    <div className="glass-panel rounded-2xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <RefreshCw className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Monitoring Schedule</h3>
            <p className="text-[10px] text-slate-500">Automated periodic crawling is active</p>
          </div>
        </div>
        {/* Pulsing ACTIVE badge */}
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/25">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[11px] text-emerald-400 font-semibold tracking-wide">ACTIVE</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
        {/* Frequency */}
        <div className="rounded-xl bg-zinc-900/50 border border-white/5 p-3">
          <p className="text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider">Frequency</p>
          <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-xs font-semibold ${cfg.color}`}>
            {cfg.icon} {cfg.label}
          </div>
        </div>
        {/* Last crawl */}
        <div className="rounded-xl bg-zinc-900/50 border border-white/5 p-3">
          <p className="text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider">Last Crawled</p>
          <p className="text-sm font-mono text-slate-200">{fmt(lastCrawledAt)}</p>
        </div>
        {/* Next crawl */}
        <div className="rounded-xl bg-zinc-900/50 border border-white/5 p-3">
          <p className="text-[10px] text-slate-500 mb-1.5 uppercase tracking-wider">Next Crawl In</p>
          <p className="text-sm font-mono text-cyan-400 font-bold">{countdown || fmt(nextCrawlAt)}</p>
        </div>
      </div>

      {/* Crawl history */}
      {crawlHistory.length > 0 && (
        <div>
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-2">Crawl History</p>
          <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
            {crawlHistory.map((log: any, i: number) => (
              <div key={i} className="flex items-center gap-3 rounded-lg bg-zinc-900/40 border border-white/[0.04] px-3 py-2">
                <span className={`w-2 h-2 rounded-full shrink-0 ${
                  log.status === 'success' ? 'bg-emerald-400' :
                  log.status === 'failed'  ? 'bg-rose-400' : 'bg-amber-400 animate-pulse'
                }`} />
                <span className="text-[11px] text-slate-400 font-mono flex-1 truncate">
                  {fmt(log.started_at)}
                </span>
                <span className={`text-[10px] font-semibold ${
                  log.status === 'success' ? 'text-emerald-400' :
                  log.status === 'failed'  ? 'text-rose-400' : 'text-amber-400'
                }`}>{log.status}</span>
                <span className="text-[10px] text-slate-600">{log.posts_found ?? 0} posts</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [allProjects, setAllProjects] = useState<{ id: number; name: string }[]>([]);
  const [showProjectPicker, setShowProjectPicker] = useState(false);
  const { fetchDashboardData, logout } = useAlgoPharmaAPI();
  const location = useLocation();
  const navigate = useNavigate();
  const initialProjectId = location.state?.projectId || localStorage.getItem('current_project_id');
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId);
  const projectId = selectedProjectId;

  useEffect(() => {
    if (!projectId) {
      navigate('/chat');
      return;
    }
    // Fetch all projects for the project switcher
    fetch('/api/results/list', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
      .then(r => r.ok ? r.json() : [])
      .then(d => setAllProjects(Array.isArray(d) ? d : []))
      .catch(() => { });

    let polling = true;
    let pollCount = 0;
    const MAX_POLLS = 75; // 75 * 4s = 5 minutes timeout

    const loadData = async () => {
      if (!polling) return;

      const res = await fetchDashboardData(projectId);

      // Stop polling if we hit an error (e.g. 404) or reached max timeout
      if (!res || pollCount >= MAX_POLLS) {
        polling = false;
        if (!res) {
          // If the project doesn't exist anymore, clear it and go back to chat
          localStorage.removeItem('current_project_id');
          navigate('/chat');
        }
        return;
      }

      setData(res);

      if (res.status === 'complete' || res.status === 'failed') {
        polling = false;
      }

      if (polling) {
        pollCount++;
        setTimeout(loadData, 4000);
      }
    };

    loadData();

    return () => {
      polling = false;
    };
  }, [projectId, fetchDashboardData, navigate]);

  // Parse medicine + source from project name e.g. "vioxx_reddit_20260515_173938"
  const parsedMeta = useMemo(() => {
    if (!data?.project_name) return { medicine: 'Unknown', source: 'Unknown' };
    const parts = data.project_name.split('_');
    // Last part is timestamp (8 digits date + _ + 6 digits time = 2 parts)
    // Format: medicine_source_YYYYMMDD_HHMMSS
    const withoutTimestamp = parts.slice(0, -2);
    const sourceParts = withoutTimestamp.filter(p => ['reddit', 'twitter', 'custom', 'forum', 'custom_forum'].includes(p.toLowerCase()));
    const medicineParts = withoutTimestamp.filter(p => !['reddit', 'twitter', 'custom', 'forum'].includes(p.toLowerCase()));
    const medicine = medicineParts.join(' ') || parts[0] || 'Unknown';
    const rawSource = sourceParts.join('_') || 'unknown';
    const sourceLabel: Record<string, string> = {
      reddit: 'Reddit', twitter: 'Twitter / X',
      custom_forum: 'Custom Forum', forum: 'Custom Forum', custom: 'Custom Forum'
    };
    return {
      medicine: medicine.charAt(0).toUpperCase() + medicine.slice(1),
      source: sourceLabel[rawSource] || rawSource,
    };
  }, [data?.project_name]);

  const handleSwitchProject = (id: number) => {
    setData(null);
    setShowProjectPicker(false);
    setSelectedProjectId(id.toString());
    localStorage.setItem('current_project_id', id.toString());
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  // Memoized Chart Data
  const sentimentData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'Positive', value: data.sentiment_distribution.positive || 0, color: COLORS.positive },
      { name: 'Neutral', value: data.sentiment_distribution.neutral || 0, color: COLORS.neutral },
      { name: 'Negative', value: data.sentiment_distribution.negative || 0, color: COLORS.negative },
    ].filter(d => d.value > 0);
  }, [data?.sentiment_distribution]);

  const aeRate = useMemo(() => {
    if (!data || data.processed === 0) return 0;
    return ((data.ae_flagged / data.processed) * 100);
  }, [data]);

  const aeData = useMemo(() => {
    if (!data) return [];
    return [
      { name: 'Adverse Events', value: data.ae_flagged, color: aeRate >= 50 ? '#ef4444' : aeRate >= 20 ? '#f59e0b' : '#10b981' },
      { name: 'Non-AE', value: Math.max(0, data.processed - data.ae_flagged), color: 'rgba(26,34,53,0.8)' },
    ].filter(d => d.value > 0);
  }, [data?.ae_flagged, data?.processed, aeRate]);

  const sourceData = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.sources).map(([name, value]) => ({ name, value }));
  }, [data?.sources]);

  const topDrugs = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.drug_counts).sort((a, b) => (b[1] as number) - (a[1] as number)).slice(0, 5);
  }, [data?.drug_counts]);

  const topSymptoms = useMemo(() => {
    if (!data) return [];
    return Object.entries(data.symptom_counts).sort((a, b) => (b[1] as number) - (a[1] as number)).slice(0, 5);
  }, [data?.symptom_counts]);

  const relationalRisk = useMemo(() => {
    if (!data || data.signals.length === 0) return null;
    const drugSymptoms: Record<string, Set<string>> = {};
    data.signals.forEach(sig => {
      if (!drugSymptoms[sig.drug]) drugSymptoms[sig.drug] = new Set();
      drugSymptoms[sig.drug].add(sig.symptom);
    });

    let maxDrug = '';
    let maxCount = 0;
    Object.entries(drugSymptoms).forEach(([drug, symptoms]) => {
      if (symptoms.size > maxCount) {
        maxCount = symptoms.size;
        maxDrug = drug;
      }
    });

    return { drug: maxDrug, count: maxCount };
  }, [data?.signals]);

  const aeGates = useMemo(() => {
    if (!data) return [];
    const gates = { ae: 0, no_drug: 0, no_symptom: 0, not_negative: 0, all_negated: 0, other: 0 };
    data.live_posts.forEach((p: any) => {
      if (p.ae_flag) { gates.ae++; return; }
      const r = p.ae_reason || '';
      if (r.includes('no_drug')) gates.no_drug++;
      else if (r.includes('no_symptom')) gates.no_symptom++;
      else if (r.includes('not_negative')) gates.not_negative++;
      else if (r.includes('all_negated')) gates.all_negated++;
      else gates.other++;
    });
    return [
      { label: 'No symptom', count: gates.no_symptom, color: 'bg-rose-500' },
      { label: 'Not negative', count: gates.not_negative, color: 'bg-rose-500' },
      { label: 'AE Confirmed', count: gates.ae, color: 'bg-emerald-500' },
    ];
  }, [data]);

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-transparent">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-cyan-500/20 flex items-center justify-center animate-pulse">
            <Activity className="w-6 h-6 text-cyan-400" />
          </div>
          <p className="text-slate-400 font-medium">Loading intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col p-4 md:p-8 space-y-6 relative bg-transparent">

      {/* Header */}
      <header className="w-full max-w-7xl mx-auto flex flex-col md:flex-row md:items-center justify-between gap-4 z-10 glass-panel p-5 rounded-2xl border border-white/5 shadow-2xl">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight flex items-center gap-3">
            <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-sm shadow-lg">⬡</span>
            Intelligence Dashboard
          </h1>
          <div className="flex flex-wrap items-center gap-3 mt-2 text-xs font-medium">
            <span className="text-slate-400">Project: <span className="font-mono text-cyan-400">#{projectId}</span></span>
            <span className="text-slate-600">•</span>
            {/* Medicine + Source */}
            <span className="flex items-center gap-1.5 text-indigo-300">
              <Pill className="w-3.5 h-3.5" />
              {parsedMeta.medicine}
            </span>
            <span className="text-slate-600">•</span>
            <span className="flex items-center gap-1.5 text-emerald-300">
              <Globe className="w-3.5 h-3.5" />
              {parsedMeta.source}
            </span>
            <span className="text-slate-600">•</span>
            <div className="flex items-center gap-2">
              <span className={`w-2 h-2 rounded-full ${data.status === 'complete' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.5)] animate-pulse'}`} />
              <span className={`${data.status === 'complete' ? 'text-emerald-400' : 'text-amber-400'}`}>
                {data.status === 'complete' ? 'Surveillance Complete' : 'Active Polling...'}
              </span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Project Switcher
          <div className="relative">
            <button
              onClick={() => setShowProjectPicker(p => !p)}
              className="flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-800 text-slate-300 hover:bg-zinc-700 transition-colors border border-white/10 text-sm font-medium"
            >
              <FileText className="w-4 h-4 text-slate-400" />
              My Projects
              <ChevronDown className={`w-3.5 h-3.5 text-slate-500 transition-transform ${showProjectPicker ? 'rotate-180' : ''}`} />
            </button>
            {showProjectPicker && (
              <div className="absolute right-0 top-full mt-2 w-72 bg-zinc-900 border border-white/10 rounded-xl shadow-2xl z-50 overflow-hidden">
                <div className="px-3 py-2 border-b border-white/5">
                  <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">Recent Projects</p>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {allProjects.length === 0 && (
                    <p className="text-xs text-slate-600 text-center py-4">No projects yet</p>
                  )}
                  {allProjects.map(p => (
                    <button
                      key={p.id}
                      onClick={() => handleSwitchProject(p.id)}
                      className={`w-full text-left px-4 py-3 text-sm hover:bg-white/5 transition-colors border-b border-white/[0.03] ${
                        p.id.toString() === projectId ? 'text-cyan-400 bg-cyan-500/5' : 'text-slate-300'
                      }`}
                    >
                      <span className="font-mono text-[10px] text-slate-500 block">#{p.id}</span>
                      <span className="truncate block">{p.name.replace(/_\d{8}_\d{6}$/, '').replace(/_/g, ' ')}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div> */}
          <button onClick={() => navigate('/chat')} className="px-4 py-2 rounded-xl bg-zinc-800 text-white hover:bg-zinc-700 transition-colors border border-white/10 text-sm font-medium shadow-md">
            New Query
          </button>
          <button onClick={handleLogout} className="px-4 py-2 rounded-xl bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-colors border border-rose-500/20 text-sm font-medium shadow-md">
            Logout
          </button>
        </div>
      </header>

      <main className="flex-1 flex flex-col gap-6 z-10 w-full max-w-7xl mx-auto">

        {/* Top Metrics Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard title="Posts Crawled" value={data.total_raw} subtext="raw data collected" color="text-indigo-400" glow="bg-indigo-500" icon={<Database className="w-4 h-4 text-indigo-400/50" />} />
          <MetricCard title="Processed" value={data.processed} subtext="NLP analysed" color="text-emerald-400" glow="bg-emerald-500" icon={<CheckCircle2 className="w-4 h-4 text-emerald-400/50" />} />
          <MetricCard
            title="Adverse Event Rate"
            value={`${aeRate.toFixed(1)}%`}
            subtext={`${data.ae_flagged} of ${data.processed} flagged`}
            color="text-amber-400"
            glow="bg-amber-500"
            icon={<AlertTriangle className="w-4 h-4 text-amber-400/50" />}
          />
          <MetricCard
            title="Relational Risk"
            value={relationalRisk ? relationalRisk.drug : 'N/A'}
            subtext={relationalRisk ? `${relationalRisk.count} associated symptoms` : 'Gathering relations...'}
            color={relationalRisk && relationalRisk.count > 3 ? 'text-rose-400' : 'text-cyan-400'}
            glow={relationalRisk && relationalRisk.count > 3 ? 'bg-rose-500' : 'bg-cyan-500'}
            icon={<ShieldAlert className={`w-4 h-4 ${relationalRisk && relationalRisk.count > 3 ? 'text-rose-400 animate-pulse' : 'text-cyan-400/50'}`} />}
          />
        </div>

        {/* ── Monitoring Schedule Card (shown only when frequency is set) ── */}
        {data.crawl_frequency && (
          <MonitoringCard
            frequency={data.crawl_frequency}
            lastCrawledAt={data.last_crawled_at}
            nextCrawlAt={data.next_crawl_at}
            crawlHistory={data.crawl_history}
          />
        )}

        {/* Charts Row */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="glass-panel p-6 rounded-2xl h-72 flex flex-col  relative">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-rose-500" /> AE Probability
            </h3>
            <div className="flex-1 min-h-0 relative">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={aeData} innerRadius="65%" outerRadius="85%" dataKey="value" stroke="none">
                    {aeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                <span className={`text-3xl font-mono font-bold ${aeRate >= 50 ? 'text-rose-500' : aeRate >= 20 ? 'text-amber-500' : 'text-emerald-500'}`}>
                  {aeRate.toFixed(1)}%
                </span>
                <span className="text-[10px] uppercase tracking-widest text-slate-500 mt-1">Adverse Events</span>
              </div>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl h-72 flex flex-col ">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-cyan-400" /> Sentiment Split
            </h3>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={sentimentData} innerRadius="55%" outerRadius="80%" dataKey="value" stroke="none">
                    {sentimentData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend verticalAlign="middle" align="right" layout="vertical" iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl h-72 flex flex-col ">
            <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-4 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-indigo-500" /> Platform
            </h3>
            <div className="flex-1 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sourceData} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" horizontal={false} />
                  <XAxis type="number" stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} tick={false} />
                  <YAxis type="category" dataKey="name" stroke="#ffffff80" fontSize={11} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{ fill: '#ffffff05' }} content={<CustomTooltip />} />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                    {sourceData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS.bars[index % COLORS.bars.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Big Chart: Signal Strength */}
        <div className="glass-panel p-6 rounded-2xl  h-80 flex flex-col">
          <h3 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-6 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-500" /> Signal Strength Distribution & PRR Scores
          </h3>
          <div className="flex-1 min-h-0">
            {data.signals.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                Waiting for signal detection...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.signals} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                  <XAxis dataKey={(sig) => `${sig.drug}/${sig.symptom}`} stroke="#ffffff40" fontSize={9} tickLine={false} axisLine={false} tickMargin={10} interval={0} angle={-15} textAnchor="end" tick={false} />
                  <YAxis stroke="#ffffff40" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip cursor={{ fill: '#ffffff05' }} content={<CustomTooltip />} />
                  <Legend verticalAlign="top" height={36} iconType="square" iconSize={8} wrapperStyle={{ fontSize: '11px', color: '#94a3b8' }} />
                  <Bar dataKey="prr" name="PRR" fill="#6366f1" radius={[2, 2, 0, 0]} />
                  <Bar dataKey="ror" name="ROR" fill="#06b6d4" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Infographics Row */}
        {data.processed > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-panel p-5 rounded-2xl ">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">AE Gate Analysis</h3>
              <div className="space-y-3.5">
                {aeGates.map(gate => (
                  <div key={gate.label} className="space-y-1.5">
                    <div className="flex justify-between text-[11px] text-slate-300">
                      <span className="flex items-center gap-1.5 uppercase tracking-wide">
                        {gate.label === 'AE Confirmed' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> : <XCircle className="w-3.5 h-3.5 text-rose-500" />}
                        {gate.label}
                      </span>
                      <span className="font-mono text-slate-500">{gate.count} / {Math.round((gate.count / data.processed) * 100)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#1e293b]/50 rounded-full overflow-hidden">
                      <div className={`h-full ${gate.color} transition-all duration-700`} style={{ width: `${(gate.count / data.processed) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl ">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Top Drugs Detected</h3>
              <div className="space-y-3.5">
                {topDrugs.map(([d, c]) => (
                  <div key={d} className="space-y-1.5">
                    <div className="flex justify-between text-[11px] text-slate-300">
                      <span className="flex items-center gap-1.5 lowercase">💊 {d}</span>
                      <span className="font-mono text-slate-500">{c as number} posts</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#1e293b]/50 rounded-full overflow-hidden">
                      <div className="h-full bg-indigo-500 transition-all duration-700" style={{ width: `${((c as number) / data.processed) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-panel p-5 rounded-2xl ">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-4">Top Symptoms Detected</h3>
              <div className="space-y-3.5">
                {topSymptoms.map(([s, c]) => (
                  <div key={s} className="space-y-1.5">
                    <div className="flex justify-between text-[11px] text-slate-300">
                      <span className="flex items-center gap-1.5 lowercase">⚕ {s}</span>
                      <span className="font-mono text-slate-500">{c as number} posts</span>
                    </div>
                    <div className="w-full h-1.5 bg-[#1e293b]/50 rounded-full overflow-hidden">
                      <div className="h-full bg-amber-500 transition-all duration-700" style={{ width: `${((c as number) / data.processed) * 100}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Signals Table */}
        <div className="glass-panel p-6 rounded-2xl  overflow-hidden flex flex-col">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-widest mb-6 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-indigo-400" /> Detected Signals
            <span className="bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full text-xs font-mono">{data.signals.length}</span>
          </h3>

          <div className="overflow-x-auto flex-1">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-slate-400 text-[11px] uppercase tracking-widest">
                  <th className="pb-3 px-4 font-semibold">Drug</th>
                  <th className="pb-3 px-4 font-semibold">Symptom</th>
                  <th className="pb-3 px-4 font-semibold text-center">Reports</th>
                  <th className="pb-3 px-4 font-semibold">PRR (Disproportionality)</th>
                  <th className="pb-3 px-4 font-semibold">ROR (Odds Ratio)</th>
                  <th className="pb-3 px-4 font-semibold">χ² Confidence</th>
                  <th className="pb-3 px-4 font-semibold">Strength</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {data.signals.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-slate-500">
                      {data.status === 'complete' ? 'No signals detected meeting criteria.' : 'Analyzing patterns...'}
                    </td>
                  </tr>
                ) : (
                  data.signals.map((sig, i) => {
                    const maxPRR = Math.max(...data.signals.map(s => s.prr), 1);
                    return (
                      <tr key={i} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td className="py-3 px-4 font-bold text-white lowercase">{sig.drug}</td>
                        <td className="py-3 px-4 text-slate-300 lowercase">{sig.symptom}</td>
                        <td className="py-3 px-4 text-slate-400 font-mono text-center text-xs">{sig.co_occurrences}</td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="w-16 h-1 bg-[#1e293b] rounded-full overflow-hidden">
                              <div className="h-full bg-cyan-400" style={{ width: `${Math.min((sig.prr / maxPRR) * 100, 100)}%` }} />
                            </div>
                            <span className="text-cyan-400 font-mono text-xs">{sig.prr.toFixed(2)}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-slate-300 font-mono text-xs">{sig.ror?.toFixed(2) || '0.00'}</td>
                        <td className="py-3 px-4 text-slate-300 font-mono text-xs">{sig.chi_square.toFixed(2)}</td>
                        <td className="py-3 px-4">
                          <span className={`px-2.5 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider border ${sig.strength === 'STRONG' ? 'bg-rose-500/10 text-rose-400 border-rose-500/20' :
                              sig.strength === 'MODERATE' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' :
                                'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                            }`}>
                            {sig.strength}
                          </span>
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Processed Posts List */}
        <div className="glass-panel p-6 rounded-2xl  flex flex-col mb-12">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-widest mb-6 flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-emerald-400" /> Processed Posts
            <span className="bg-indigo-500/20 text-indigo-400 px-2 py-0.5 rounded-full text-xs font-mono">{data.live_posts.length}</span>
          </h3>

          <div className="h-[600px] overflow-y-auto space-y-3 pr-4 custom-scrollbar">
            <AnimatePresence>
              {data.live_posts.length === 0 ? (
                <div className="h-full flex items-center justify-center text-slate-500 text-sm">
                  Posts will appear as they are processed...
                </div>
              ) : data.live_posts.map((post: any, idx: number) => {
                const isPositive = post.sentiment?.toUpperCase() === 'POSITIVE';
                const isNegative = post.sentiment?.toUpperCase() === 'NEGATIVE';
                const sentimentColor = isPositive ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' : isNegative ? 'text-rose-400 bg-rose-500/10 border-rose-500/20' : 'text-slate-400 bg-slate-500/10 border-slate-500/20';

                return (
                  <motion.div
                    key={post.id || idx}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`p-5 rounded-xl border relative bg-[#0d1220]/60 ${post.ae_flag ? 'border-l-[3px] border-l-rose-500 border-white/5' : 'border-l-[3px] border-l-emerald-500 border-white/5'}`}
                  >
                    <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] uppercase tracking-widest font-bold text-indigo-400 bg-indigo-500/10 px-2 py-1 rounded border border-indigo-500/20">
                          {post.platform || 'UNKNOWN'}
                        </span>
                        <span className={`text-[10px] uppercase tracking-widest font-bold px-2 py-1 rounded border ${sentimentColor}`}>
                          {post.sentiment || 'NEUTRAL'}
                        </span>
                        {post.ae_flag && (
                          <span className="flex items-center gap-1.5 text-[10px] text-rose-400 font-bold bg-rose-500/10 px-2 py-1 rounded border border-rose-500/20 tracking-widest">
                            <AlertTriangle className="w-3.5 h-3.5" /> AE DETECTED
                          </span>
                        )}
                      </div>
                      <span className="text-xs font-mono text-slate-500">#{idx + 1}</span>
                    </div>

                    {post.title && <h4 className="text-sm font-semibold text-white mb-2">{post.title}</h4>}
                    <p className="text-[13px] text-slate-300 leading-relaxed mb-4">{post.text}</p>

                    {(post.drugs?.length > 0 || post.symptoms?.length > 0 || post.ae_reason) && (
                      <div className="flex flex-wrap gap-2 mt-2 pt-3 border-t border-white/5">
                        {post.drugs?.map((d: string, i: number) => (
                          <span key={`d-${i}`} className="text-[10px] uppercase tracking-widest font-bold text-indigo-300 bg-indigo-500/10 border border-indigo-500/20 px-2 py-1 rounded">
                            💊 {d}
                          </span>
                        ))}
                        {post.symptoms?.map((s: string, i: number) => (
                          <span key={`s-${i}`} className="text-[10px] uppercase tracking-widest font-bold text-amber-300 bg-amber-500/10 border border-amber-500/20 px-2 py-1 rounded">
                            ⚕ {s}
                          </span>
                        ))}
                        {post.ae_reason && (
                          <span className="text-[10px] uppercase tracking-widest font-medium text-slate-400 bg-slate-800/50 border border-slate-700/50 px-2 py-1 rounded italic">
                            {post.ae_reason}
                          </span>
                        )}
                      </div>
                    )}

                    {/* Confidence Bar */}
                    {post.ae_confidence !== undefined && (
                      <div className="flex items-center gap-2 mt-4">
                        <div className="flex-1 h-1 bg-[#1e293b]/50 rounded-full overflow-hidden">
                          <div className={`h-full ${post.ae_confidence >= 0.7 ? 'bg-rose-500' : post.ae_confidence >= 0.4 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${post.ae_confidence * 100}%` }} />
                        </div>
                        <span className="text-[10px] font-mono text-slate-500">{(post.ae_confidence * 100).toFixed(1)}% CONFIDENCE</span>
                      </div>
                    )}
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </div>

      </main>
    </div>
  );
}

// Custom Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-[#0d1220]/90 backdrop-blur-md px-4 py-3 rounded-xl border border-white/10 shadow-2xl">
        {label && <p className="text-slate-300 font-medium mb-1 text-xs uppercase tracking-wider">{label}</p>}
        {payload.map((p: any, i: number) => (
          <p key={i} className="text-sm font-mono" style={{ color: p.color || p.fill }}>
            {p.name}: {p.value.toFixed ? p.value.toFixed(2) : p.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Helper component
function MetricCard({ title, value, subtext, color, glow, icon }: any) {
  return (
    <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between  relative overflow-hidden group">
      <div className={`absolute -right-8 -top-8 w-24 h-24 rounded-full ${glow || 'bg-indigo-500'} opacity-5 group-hover:opacity-10 transition-opacity blur-xl`} />
      <div className="flex items-center justify-between mb-3 z-10">
        <h3 className="text-slate-400 font-bold text-[11px] uppercase tracking-widest">{title}</h3>
        {icon}
      </div>
      <div className="z-10">
        <p className={`text-[32px] font-mono font-bold ${color || 'text-white'} tracking-tighter leading-none mb-1`}>{value}</p>
        {subtext && <p className="text-[11px] text-slate-500">{subtext}</p>}
      </div>
    </div>
  );
}
