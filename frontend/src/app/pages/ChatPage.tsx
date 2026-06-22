import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router';
import { motion, AnimatePresence } from 'motion/react';
import {
  Send, Activity, ShieldAlert, Bot, User, Loader2, LogOut,
  Globe, Twitter, MessageCircle, LayoutDashboard, ChevronRight, Clock,
  Zap, Calendar, CalendarDays
} from 'lucide-react';
import { useAlgoPharmaAPI } from '../hooks/useAlgoPharmaAPI';

interface Message { id: string; type: 'user' | 'bot'; content: string; }
interface CustomForum { id: number; name: string; url: string; platform: string; }
interface Project { id: number; name: string; created_at: string; }

const isAskingForSource = (msg: string) =>
  /where.*search|choose.*source|reddit.*twitter.*forum|platform/i.test(msg);

// Read forum name map from localStorage
const getForumMap = (): Record<string, string> => {
  try { return JSON.parse(localStorage.getItem('project_forum_map') || '{}'); } catch { return {}; }
};

function parseProjectLabel(name: string, id: number) {
  const forumMap = getForumMap();
  const parts = name.split('_');
  const withoutTs = parts.slice(0, -2);
  const srcWords = ['reddit', 'twitter', 'custom', 'forum'];
  const med = withoutTs.filter(p => !srcWords.includes(p.toLowerCase())).join(' ');
  const src = withoutTs.filter(p => srcWords.includes(p.toLowerCase())).join('_');
  const srcLabel: Record<string, string> = {
    reddit: 'Reddit', twitter: 'Twitter', custom_forum: 'Forum', forum: 'Forum', custom: 'Forum'
  };
  // Use stored forum name if available
  const forumName = forumMap[id.toString()];
  return {
    medicine: med ? med.charAt(0).toUpperCase() + med.slice(1) : name,
    source: forumName || srcLabel[src] || src || '?',
  };
}

const FREQUENCY_OPTIONS = [
  { key: 'realtime', label: 'Real-time', desc: 'Crawl continuously', icon: Zap, color: 'text-cyan-300 border-cyan-500/25 bg-cyan-500/10 hover:bg-cyan-500/20' },
  { key: 'daily', label: 'Daily', desc: 'Once per day', icon: Calendar, color: 'text-indigo-300 border-indigo-500/25 bg-indigo-500/10 hover:bg-indigo-500/20' },
  { key: 'weekly', label: 'Weekly', desc: 'Once per week', icon: CalendarDays, color: 'text-violet-300 border-violet-500/25 bg-violet-500/10 hover:bg-violet-500/20' },
];

const renderMarkdown = (text: string) => {
  if (!text) return null;
  const parts = text.split(/(\*\*.*?\*\*|\*.*?\*)/g);
  return (
    <>
      {parts.map((part, idx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={idx} className="font-extrabold text-white">{part.slice(2, -2)}</strong>;
        }
        if (part.startsWith('*') && part.endsWith('*')) {
          return <em key={idx} className="italic text-slate-300">{part.slice(1, -1)}</em>;
        }
        return part;
      })}
    </>
  );
};

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', type: 'bot', content: 'Welcome to AlgoPharma Intelligence. Enter a drug name to begin adverse event surveillance.' }
  ]);
  const [input, setInput] = useState('');
  const [customForums, setCustomForums] = useState<CustomForum[]>([]);
  const [showSourcePicker, setShowSourcePicker] = useState(false);
  const [showFrequencyPicker, setShowFrequencyPicker] = useState(false);
  const [pendingForumName, setPendingForumName] = useState('');
  const [projects, setProjects] = useState<Project[]>([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const { sendChat, logout, loading, error, isAuthenticated, role } = useAlgoPharmaAPI();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) { navigate('/login'); return; }
    localStorage.removeItem('chat_state');
    fetchCustomForums();
    fetchProjects();
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, [messages]);

  const fetchCustomForums = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/admin/sources/available', { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (res.ok) { const d = await res.json(); setCustomForums(Array.isArray(d) ? d : []); }
    } catch { }
  };

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch('/api/results/list', { headers: token ? { Authorization: `Bearer ${token}` } : {} });
      if (res.ok) { const d = await res.json(); setProjects(Array.isArray(d) ? d : []); }
    } catch { }
  };

  const addBotMsg = (content: string) =>
    setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', content }]);

  const sendMessage = useCallback(async (userMessage: string) => {
    setMessages(prev => [...prev, { id: Date.now().toString(), type: 'user', content: userMessage }]);
    setShowSourcePicker(false);
    const result = await sendChat(userMessage);
    if (result) {
      addBotMsg(result.bot_message);
      if (!result.ready && isAskingForSource(result.bot_message)) setShowSourcePicker(true);
      if (result.ready && result.project_id) {
        setShowSourcePicker(false);
        setShowFrequencyPicker(false);
        // Store forum name mapped to project_id
        if (pendingForumName) {
          const map = getForumMap();
          map[result.project_id.toString()] = pendingForumName;
          localStorage.setItem('project_forum_map', JSON.stringify(map));
          setPendingForumName('');
        }
        fetchProjects();
        setTimeout(() => navigate('/processing', { state: { projectId: result.project_id } }), 1500);
      }
    } else if (error) {
      addBotMsg(`Error: ${error}`);
    }
  }, [sendChat, error, navigate, pendingForumName]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input.trim(); setInput('');
    await sendMessage(msg);
  };

  const handleSourcePick = async (sourceName: string, key: string, forumId?: number, forumUrl?: string, forumName?: string) => {
    setShowSourcePicker(false);
    // Inject custom forum state if needed
    if (forumId && forumUrl) {
      const stateStr = localStorage.getItem('chat_state');
      const state = stateStr ? JSON.parse(stateStr) : {};
      state.source = 'custom_forum'; state.source_id = forumId; state.forum_url = forumUrl;
      localStorage.setItem('chat_state', JSON.stringify(state));
    }
    // Always store pending forum/source name and show frequency picker
    setPendingForumName(forumName || sourceName);
    setShowFrequencyPicker(true);
    setMessages(prev => [...prev, { id: Date.now().toString(), type: 'user', content: sourceName }]);
    addBotMsg(`How often should I crawl **${forumName || sourceName}** for new posts?`);
  };

  const handleFrequencyPick = async (freq: typeof FREQUENCY_OPTIONS[0]) => {
    setShowFrequencyPicker(false);
    // Store frequency in chat state so backend can persist it on the project
    const stateStr = localStorage.getItem('chat_state');
    const state = stateStr ? JSON.parse(stateStr) : {};
    state.crawl_frequency = freq.key;
    localStorage.setItem('chat_state', JSON.stringify(state));
    // Show the frequency choice in chat (UI confirmation)
    setMessages(prev => [...prev, { id: Date.now().toString(), type: 'user', content: freq.label }]);
    addBotMsg(`Got it — **${freq.label}** monitoring selected. Starting analysis on ${pendingForumName}...`);
    
    // Call sendChat directly to start the project crawl on the backend,
    // without printing the source name in the chat UI a second time
    const result = await sendChat(pendingForumName);
    if (result) {
      addBotMsg(result.bot_message);
      if (result.ready && result.project_id) {
        setShowSourcePicker(false);
        setShowFrequencyPicker(false);
        if (pendingForumName) {
          const map = getForumMap();
          map[result.project_id.toString()] = pendingForumName;
          localStorage.setItem('project_forum_map', JSON.stringify(map));
          setPendingForumName('');
        }
        fetchProjects();
        setTimeout(() => navigate('/processing', { state: { projectId: result.project_id } }), 1500);
      }
    } else if (error) {
      addBotMsg(`Error: ${error}`);
    }
  };

  const openProject = (id: number) => {
    localStorage.setItem('current_project_id', id.toString());
    navigate('/dashboard', { state: { projectId: id.toString() } });
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="glass-panel-subtle sticky top-0 z-20 flex items-center justify-between px-6 py-3.5 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-gradient-to-br from-cyan-400 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-4.5 h-4.5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight leading-none">AlgoPharma</h1>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-[10px] text-slate-500 font-medium">Online</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <div className="px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/15 flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-[10px] text-cyan-400 font-medium tracking-wide uppercase">{role || 'viewer'}</span>
          </div>
          {role === 'admin' && (
            <button onClick={() => navigate('/admin')} className="px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center gap-1.5 hover:bg-indigo-500/20 transition-colors">
              <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-[10px] text-indigo-400 font-medium tracking-wide">ADMIN</span>
            </button>
          )}
          <button onClick={() => { logout(); navigate('/login'); }} className="px-3 py-1.5 rounded-full bg-rose-500/8 border border-rose-500/15 flex items-center gap-1.5 hover:bg-rose-500/15 transition-colors">
            <LogOut className="w-3.5 h-3.5 text-rose-400" />
            <span className="text-[10px] text-rose-400 font-medium tracking-wide">LOGOUT</span>
          </button>
        </div>
      </header>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden relative">

        {/* Sidebar */}
        <AnimatePresence initial={false}>
          {sidebarOpen && (
            <motion.aside
              key="sidebar"
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 260, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              transition={{ duration: 0.22 }}
              className="shrink-0 border-r border-white/5 bg-zinc-950/60 backdrop-blur-md flex flex-col overflow-hidden z-10"
            >
              <div className="px-4 py-3 border-b border-white/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <LayoutDashboard className="w-3.5 h-3.5 text-cyan-400" />
                  <span className="text-[11px] text-slate-400 font-semibold uppercase tracking-wider">My Projects</span>
                </div>
                <span className="text-[10px] font-mono text-slate-600">{projects.length}</span>
              </div>
              <div className="flex-1 overflow-y-auto py-2">
                {projects.length === 0 ? (
                  <p className="text-xs text-slate-600 text-center py-6 px-4">No projects yet. Start a query to create one.</p>
                ) : projects.map(p => {
                  const { medicine, source } = parseProjectLabel(p.name, p.id);
                  const dateStr = p.created_at ? new Date(p.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' }) : '';
                  return (
                    <button key={p.id} onClick={() => openProject(p.id)}
                      className="w-full text-left px-4 py-3 hover:bg-white/[0.04] transition-colors border-b border-white/[0.03] group">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-white text-xs font-semibold capitalize truncate max-w-[160px]">{medicine}</span>
                        <ChevronRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-cyan-400 transition-colors shrink-0" />
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-cyan-500 bg-cyan-500/10 border border-cyan-500/20 px-1.5 py-0.5 rounded font-medium truncate max-w-[140px]">{source}</span>
                        {dateStr && <span className="flex items-center gap-1 text-[10px] text-slate-600 shrink-0"><Clock className="w-3 h-3" />{dateStr}</span>}
                      </div>
                    </button>
                  );
                })}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Sidebar toggle */}
        <motion.button
          animate={{ left: sidebarOpen ? 260 : 0 }}
          transition={{ duration: 0.22 }}
          onClick={() => setSidebarOpen(o => !o)}
          className="absolute top-1/2 -translate-y-1/2 z-20 w-5 h-10 bg-zinc-800 border border-white/10 rounded-r-lg flex items-center justify-center hover:bg-zinc-700 transition-colors"
        >
          <ChevronRight className={`w-3 h-3 text-slate-400 transition-transform ${sidebarOpen ? 'rotate-180' : ''}`} />
        </motion.button>

        {/* Chat */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main ref={chatContainerRef} className="flex-1 overflow-y-auto p-4 md:p-8 z-10">
            <div className="max-w-3xl mx-auto space-y-6">
              <AnimatePresence>
                {messages.map((msg) => (
                  <motion.div key={msg.id} initial={{ opacity: 0, y: 10, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }}
                    className={`flex gap-4 ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ${msg.type === 'user' ? 'bg-zinc-800 border border-white/10 text-slate-300' : 'bg-gradient-to-br from-cyan-500 to-indigo-500 text-white'}`}>
                      {msg.type === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                    </div>
                    <div className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-xl backdrop-blur-md ${msg.type === 'user' ? 'bg-zinc-800/80 border border-white/5 text-slate-200 rounded-tr-sm' : 'bg-zinc-900/60 border border-cyan-500/20 text-slate-200 rounded-tl-sm'}`}>
                      <p className="leading-relaxed whitespace-pre-wrap">{renderMarkdown(msg.content)}</p>
                    </div>
                  </motion.div>
                ))}

                {/* Source Picker */}
                {showSourcePicker && !loading && (
                  <motion.div key="source-picker" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-500 text-white flex items-center justify-center shrink-0"><Bot className="w-5 h-5" /></div>
                    <div className="bg-zinc-900/60 border border-cyan-500/20 rounded-2xl rounded-tl-sm px-5 py-4 space-y-3 max-w-[80%]">
                      <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Pick a source</p>
                      <div className="flex flex-wrap gap-2">
                        <button onClick={() => handleSourcePick('Reddit', 'reddit')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-orange-500/10 border border-orange-500/25 text-orange-300 hover:bg-orange-500/20 text-sm font-medium transition-all">
                          <MessageCircle className="w-4 h-4" /> Reddit
                        </button>
                        <button onClick={() => handleSourcePick('Twitter', 'twitter')} className="flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-500/10 border border-sky-500/25 text-sky-300 hover:bg-sky-500/20 text-sm font-medium transition-all">
                          <Twitter className="w-4 h-4" /> Twitter / X
                        </button>
                        {customForums.map(forum => (
                          <button key={forum.id} onClick={() => handleSourcePick(forum.name, 'custom_forum', forum.id, forum.url, forum.name)}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/25 text-emerald-300 hover:bg-emerald-500/20 text-sm font-medium transition-all">
                            <Globe className="w-4 h-4" /> {forum.name}
                          </button>
                        ))}
                        {customForums.length === 0 && <span className="text-xs text-slate-600 italic self-center">No custom forums configured yet.</span>}
                      </div>
                    </div>
                  </motion.div>
                )}

                {/* Crawl Frequency Picker */}
                {showFrequencyPicker && !loading && (
                  <motion.div key="freq-picker" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-500 text-white flex items-center justify-center shrink-0"><Bot className="w-5 h-5" /></div>
                    <div className="bg-zinc-900/60 border border-cyan-500/20 rounded-2xl rounded-tl-sm px-5 py-4 space-y-3 max-w-[80%]">
                      <p className="text-slate-400 text-xs font-medium uppercase tracking-wider">Crawl Frequency</p>
                      <div className="flex flex-wrap gap-2">
                        {FREQUENCY_OPTIONS.map(opt => {
                          const Icon = opt.icon;
                          return (
                            <button key={opt.key} onClick={() => handleFrequencyPick(opt)}
                              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl border text-sm font-medium transition-all ${opt.color}`}>
                              <Icon className="w-4 h-4" />
                              <div className="text-left">
                                <div className="font-semibold leading-none">{opt.label}</div>
                                <div className="text-[10px] opacity-70 mt-0.5">{opt.desc}</div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </motion.div>
                )}

                {loading && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-500 text-white flex items-center justify-center shrink-0"><Bot className="w-5 h-5" /></div>
                    <div className="bg-zinc-900/60 border border-cyan-500/20 rounded-2xl rounded-tl-sm px-6 py-4 flex items-center gap-2">
                      <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                      <span className="text-slate-400 text-sm">Analyzing intelligence...</span>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </main>

          <footer className="glass-panel-subtle sticky bottom-0 z-20 border-t border-white/5 p-4">
            <div className="max-w-3xl mx-auto">
              <form onSubmit={handleSubmit} className="relative">
                <input type="text" value={input} onChange={e => setInput(e.target.value)}
                  placeholder="e.g. Find adverse events for Aspirin..."
                  className="w-full bg-zinc-900/50 border border-white/10 rounded-2xl py-4 pl-6 pr-16 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all shadow-inner"
                  disabled={loading} />
                <button type="submit" disabled={!input.trim() || loading}
                  className="absolute right-2 top-2 bottom-2 w-12 flex items-center justify-center bg-cyan-500 hover:bg-cyan-400 text-zinc-950 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                  <Send className="w-5 h-5" />
                </button>
              </form>
              <div className="mt-3 flex justify-center gap-4">
                <button type="button" onClick={() => setInput('Analyze Aspirin')} className="text-xs text-slate-500 hover:text-cyan-400 transition-colors border border-white/5 bg-zinc-900/50 rounded-full px-3 py-1">Try "Analyze Aspirin"</button>
                <button type="button" onClick={() => setInput('Find issues with Ibuprofen')} className="text-xs text-slate-500 hover:text-cyan-400 transition-colors border border-white/5 bg-zinc-900/50 rounded-full px-3 py-1">Try "Find issues with Ibuprofen"</button>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </div>
  );
}
