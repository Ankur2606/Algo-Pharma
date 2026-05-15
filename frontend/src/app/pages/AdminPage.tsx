import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router';
import { motion } from 'motion/react';
import { 
  Shield, Server, Users, Key, Plus, Activity, 
  Play, CheckCircle2, Loader2, Link as LinkIcon,
  LogOut, MessageSquare, RefreshCw
} from 'lucide-react';
import { useAlgoPharmaAPI } from '../hooks/useAlgoPharmaAPI';

export function AdminPage() {
  const { 
    isAuthenticated, role, fetchAdminSources, testAdminSource, saveAdminSource,
    runAgenticOnboarding, fetchAdminUsers, toggleUserRole, updateCredentials, logout
  } = useAlgoPharmaAPI();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'sources'|'onboarding'|'users'|'infra'>('sources');
  const [sources, setSources] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Forms state prefilled for POC
  const [sourceForm, setSourceForm] = useState({ name: 'MedHelp Cardiology', platform: 'forum', url: 'https://www.medhelp.org/forums/Cardiology/show/41', config_json: '{"test": true}' });
  const [onboardingUrl, setOnboardingUrl] = useState('https://www.medhelp.org/forums/Cardiology/show/41');
  const [infraKey, setInfraKey] = useState('GROQ_API_KEY');
  const [infraValue, setInfraValue] = useState('gsk-xxxxxx');
  
  const [testResult, setTestResult] = useState<any>(null);
  const [onboardResult, setOnboardResult] = useState<any>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else if (role !== 'admin') {
      navigate('/chat');
    } else {
      loadInitialData();
    }
  }, [isAuthenticated, role, navigate]);

  const loadInitialData = async () => {
    setLoading(true);
    const s = await fetchAdminSources();
    setSources(Array.isArray(s) ? s : []);
    const u = await fetchAdminUsers();
    setUsers(Array.isArray(u) ? u : []);
    setLoading(false);
  };

  const handleTestSource = async () => {
    setLoading(true);
    // Map 'forum' (dropdown value) to 'custom_forum' (backend platform name)
    const platform = sourceForm.platform === 'forum' ? 'custom_forum' : sourceForm.platform;
    const result = await testAdminSource(sourceForm.url, sourceForm.config_json, platform);
    setTestResult(result);
    setLoading(false);
  };

  const handleSaveSource = async () => {
    setLoading(true);
    await saveAdminSource(sourceForm.name, sourceForm.platform, sourceForm.url, sourceForm.config_json);
    await loadInitialData();
    setLoading(false);
    setTestResult(null);
  };

  const handleAgenticOnboard = async () => {
    setLoading(true);
    const result = await runAgenticOnboarding(onboardingUrl);
    setOnboardResult(result);
    setLoading(false);
  };

  const handleToggleRole = async (userId: number, currentRole: string) => {
    await toggleUserRole(userId, currentRole);
    await loadInitialData();
  };

  const handleUpdateInfra = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    await updateCredentials(infraKey, infraValue);
    alert('Infrastructure config updated');
    setLoading(false);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (role !== 'admin') {
    return <div className="min-h-screen bg-[#050810] flex items-center justify-center text-white">Unauthorized</div>;
  }

  const tabs = [
    { key: 'sources', label: 'Sources', icon: <Server className="w-4 h-4" /> },
    { key: 'onboarding', label: 'Onboarding', icon: <Play className="w-4 h-4" /> },
    { key: 'users', label: 'Users', icon: <Users className="w-4 h-4" /> },
    { key: 'infra', label: 'Config', icon: <Key className="w-4 h-4" /> },
  ] as const;

  return (
    <div className="min-h-screen bg-[#050810] text-slate-300 relative overflow-hidden flex flex-col">

      {/* ── Dark Checkerboard BG ── */}
      <div className="absolute inset-0 z-0 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(45deg, rgba(255,255,255,0.008) 25%, transparent 25%),
          linear-gradient(-45deg, rgba(255,255,255,0.008) 25%, transparent 25%),
          linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.008) 75%),
          linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.008) 75%)
        `,
        backgroundSize: '36px 36px',
        backgroundPosition: '0 0, 0 18px, 18px -18px, -18px 0px',
      }} />

      {/* ── Neon Glow Orbs ── */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-cyan-500/5 rounded-full blur-[160px] pointer-events-none" />
      <div className="absolute bottom-0 right-0 w-[400px] h-[400px] bg-indigo-500/5 rounded-full blur-[140px] pointer-events-none" />

      {/* ── Top Navbar ── */}
      <nav className="sticky top-0 z-30 w-full flex items-center justify-between px-6 py-3 border-b border-cyan-500/[0.06] bg-[#050810]/90 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-indigo-500 rounded-lg flex items-center justify-center shadow-[0_0_16px_rgba(6,182,212,0.2)]">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <div>
            <span className="text-white font-bold text-sm tracking-tight">Admin Console</span>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(6,182,212,0.5)]" />
              <span className="text-[9px] text-cyan-500/60 font-medium tracking-wider uppercase">Secured</span>
            </div>
          </div>
        </div>

        {/* Tab Navigation — Inline in navbar */}
        <div className="flex items-center gap-0.5 p-0.5 bg-zinc-900/60 border border-white/[0.04] rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-[11px] font-medium transition-all duration-200 ${
                activeTab === tab.key
                  ? 'bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 shadow-[0_0_8px_rgba(6,182,212,0.08)]'
                  : 'text-slate-600 hover:text-slate-400'
              }`}
            >
              {tab.icon}
              <span className="hidden md:inline">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => navigate('/chat')}
            className="px-3 py-1.5 rounded-full bg-zinc-800/60 border border-white/[0.06] flex items-center gap-1.5 hover:bg-zinc-700/60 transition-colors"
          >
            <MessageSquare className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-[10px] text-slate-400 font-medium">Chat</span>
          </button>
          <button
            onClick={handleLogout}
            className="px-3 py-1.5 rounded-full bg-rose-500/8 border border-rose-500/15 flex items-center gap-1.5 hover:bg-rose-500/15 transition-colors"
          >
            <LogOut className="w-3.5 h-3.5 text-rose-400" />
            <span className="text-[10px] text-rose-400 font-medium">Logout</span>
          </button>
        </div>
      </nav>

      {/* ── Main Content ── */}
      <main className="flex-1 p-6 md:p-8 z-10 overflow-y-auto">
        <motion.div 
          key={activeTab}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="max-w-6xl mx-auto space-y-6"
        >
          {/* ──────── SOURCES ──────── */}
          {activeTab === 'sources' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <div className="w-1.5 h-5 rounded-full bg-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.4)]" />
                  Source Management
                </h2>
                <button onClick={loadInitialData} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Add Source Form */}
                <div className="bg-zinc-900/40 backdrop-blur-sm p-6 rounded-2xl border border-white/[0.06]">
                  <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2"><Plus className="w-4 h-4 text-cyan-400"/> Add New Source</h3>
                  <div className="space-y-3">
                    <input type="text" value={sourceForm.name} onChange={e => setSourceForm({...sourceForm, name: e.target.value})} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30" placeholder="Source Name" />
                    <select value={sourceForm.platform} onChange={e => setSourceForm({...sourceForm, platform: e.target.value})} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30">
                      <option value="custom_forum">Medical Forum</option>
                      <option value="reddit">Reddit</option>
                      <option value="twitter">Twitter / X</option>
                    </select>
                    <input type="text" value={sourceForm.url} onChange={e => setSourceForm({...sourceForm, url: e.target.value})} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30" placeholder="Target URL" />
                    <textarea value={sourceForm.config_json} onChange={e => setSourceForm({...sourceForm, config_json: e.target.value})} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30 h-28 font-mono text-xs" placeholder="Configuration JSON" />
                    <div className="flex gap-2 pt-1">
                      <button onClick={handleTestSource} disabled={loading} className="flex-1 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 border border-indigo-500/20 rounded-lg py-2 text-xs font-medium transition-all flex items-center justify-center gap-1.5">
                        {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin"/> : <Activity className="w-3.5 h-3.5"/>} Test
                      </button>
                      <button onClick={handleSaveSource} disabled={loading} className="flex-1 bg-cyan-500/10 text-cyan-300 hover:bg-cyan-500/20 border border-cyan-500/20 rounded-lg py-2 text-xs font-medium transition-all flex items-center justify-center gap-1.5">
                        <CheckCircle2 className="w-3.5 h-3.5"/> Save
                      </button>
                    </div>
                  </div>
                  {testResult && (
                    <div className="mt-4 p-3 bg-zinc-950/50 rounded-lg border border-white/5 overflow-x-auto">
                      <pre className="text-[10px] text-green-400 font-mono">{JSON.stringify(testResult, null, 2)}</pre>
                    </div>
                  )}
                </div>

                {/* Active Sources List */}
                <div className="bg-zinc-900/40 backdrop-blur-sm p-6 rounded-2xl border border-white/[0.06]">
                  <h3 className="text-sm font-semibold text-white mb-4">Active Sources</h3>
                  <div className="space-y-2.5 overflow-y-auto max-h-[500px] pr-1">
                    {sources.map((src: any) => (
                      <div key={src.id} className="p-3.5 bg-zinc-950/40 rounded-xl border border-white/[0.04] flex flex-col gap-1.5">
                        <div className="flex justify-between items-start">
                          <h4 className="text-white text-sm font-medium">{src.name}</h4>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${src.is_active ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/15 text-red-400 border border-red-500/20'}`}>
                            {src.is_active ? 'Active' : 'Off'}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[10px] text-slate-500">
                          <span className="uppercase text-cyan-500 font-medium">{src.platform}</span>
                          <span>•</span>
                          <span className="truncate max-w-[200px]" title={src.url}>{src.url}</span>
                        </div>
                      </div>
                    ))}
                    {sources.length === 0 && <p className="text-xs text-slate-600 text-center py-6">No sources yet. Add one above.</p>}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ──────── ONBOARDING ──────── */}
          {activeTab === 'onboarding' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <div className="w-1.5 h-5 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(99,102,241,0.4)]" />
                Agentic Forum Onboarding
              </h2>
              <div className="bg-zinc-900/40 backdrop-blur-sm p-6 rounded-2xl border border-white/[0.06] max-w-2xl">
                <p className="text-slate-500 mb-5 text-xs leading-relaxed">
                  Provide a seed URL to a medical forum. The AI agent will crawl the site, analyze the DOM structure, 
                  and generate a configuration template automatically.
                </p>
                <div className="flex gap-3 mb-5">
                  <div className="flex-1 relative">
                    <LinkIcon className="absolute left-3.5 top-2.5 w-4 h-4 text-slate-600" />
                    <input type="text" value={onboardingUrl} onChange={e => setOnboardingUrl(e.target.value)} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg pl-10 pr-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/30" placeholder="Forum URL" />
                  </div>
                  <button onClick={handleAgenticOnboard} disabled={loading} className="bg-indigo-500/15 text-indigo-300 hover:bg-indigo-500/25 border border-indigo-500/20 px-5 rounded-lg flex items-center gap-2 text-xs font-medium transition-all">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Run Agent
                  </button>
                </div>

                {onboardResult && (
                  <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="p-4 bg-zinc-950/50 rounded-lg border border-indigo-500/15 overflow-x-auto">
                    <h4 className="text-indigo-400 text-[10px] mb-2 font-bold uppercase tracking-wider">Agent Report</h4>
                    <pre className="text-[10px] text-slate-400 font-mono">{JSON.stringify(onboardResult, null, 2)}</pre>
                  </motion.div>
                )}
              </div>
            </div>
          )}

          {/* ──────── USERS ──────── */}
          {activeTab === 'users' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  <div className="w-1.5 h-5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
                  User Management
                </h2>
                <button onClick={loadInitialData} className="p-2 rounded-lg hover:bg-white/5 transition-colors">
                  <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
                </button>
              </div>
              <div className="bg-zinc-900/40 backdrop-blur-sm p-5 rounded-2xl border border-white/[0.06]">
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="border-b border-white/[0.06] text-[10px] text-slate-500 uppercase tracking-wider">
                        <th className="pb-3 px-4 font-medium">Username</th>
                        <th className="pb-3 px-4 font-medium">Email</th>
                        <th className="pb-3 px-4 font-medium">Role</th>
                        <th className="pb-3 px-4 font-medium">Status</th>
                        <th className="pb-3 px-4 font-medium">Projects</th>
                        <th className="pb-3 px-4 font-medium text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u: any) => (
                        <tr key={u.id} className="border-b border-white/[0.03] hover:bg-white/[0.02] transition-colors">
                          <td className="py-3.5 px-4 text-white text-sm font-medium">{u.email || u.username}</td>
                          <td className="py-3.5 px-4 text-sm text-slate-400">{u.email}</td>
                          <td className="py-3.5 px-4">
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                              u.role === 'admin' 
                                ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/20' 
                                : 'bg-slate-500/10 text-slate-400 border border-slate-500/20'
                            }`}>
                              {u.role?.toUpperCase() || 'VIEWER'}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                              u.is_active !== false
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}>
                              {u.is_active !== false ? 'Active' : 'Disabled'}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-xs text-slate-500 font-mono">{u.project_count ?? 0}</td>
                          <td className="py-3.5 px-4 text-right">
                            <button onClick={() => handleToggleRole(u.id, u.role)} className="text-[10px] bg-zinc-800/60 hover:bg-zinc-700/60 text-slate-300 px-3 py-1 rounded-md transition-all border border-white/[0.06] font-medium">
                              Toggle Role
                            </button>
                          </td>
                        </tr>
                      ))}
                      {users.length === 0 && (
                        <tr><td colSpan={6} className="text-center py-8 text-slate-600 text-xs">No users found. Register one to see it here.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* ──────── INFRA / CONFIG ──────── */}
          {activeTab === 'infra' && (
            <div className="space-y-6">
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <div className="w-1.5 h-5 rounded-full bg-amber-400 shadow-[0_0_8px_rgba(245,158,11,0.4)]" />
                Security & Infrastructure
              </h2>
              <div className="bg-zinc-900/40 backdrop-blur-sm p-6 rounded-2xl border border-white/[0.06] max-w-2xl">
                <form onSubmit={handleUpdateInfra} className="space-y-4">
                  <div>
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1.5">Configuration Key</label>
                    <select value={infraKey} onChange={e => setInfraKey(e.target.value)} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30">
                      <option value="GROQ_API_KEY">Groq API Key</option>
                      <option value="GEMINI_API_KEY">Gemini API Key</option>
                      <option value="DATABASE_URL">Database URL</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] text-slate-500 uppercase tracking-wider font-medium mb-1.5">Configuration Value</label>
                    <input type="text" value={infraValue} onChange={e => setInfraValue(e.target.value)} className="w-full bg-zinc-800/50 border border-white/[0.06] rounded-lg px-3.5 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500/30 font-mono" />
                  </div>
                  <button type="submit" disabled={loading} className="bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-400 hover:to-indigo-400 text-white font-semibold rounded-lg py-2.5 px-5 transition-all flex items-center justify-center gap-2 text-sm shadow-[0_0_16px_rgba(6,182,212,0.1)]">
                    {loading && <Loader2 className="w-4 h-4 animate-spin"/>} Update Configuration
                  </button>
                </form>
              </div>
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
