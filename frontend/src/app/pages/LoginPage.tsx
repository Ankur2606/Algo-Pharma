import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { motion, AnimatePresence } from 'motion/react';
import { Shield, Lock, Loader2, Mail, ShieldCheck, UserCircle, ArrowRight } from 'lucide-react';
import { useAlgoPharmaAPI } from '../hooks/useAlgoPharmaAPI';

const PRESETS = {
  admin: {
    login:    { username: 'admin@example.com', password: 'admin123' },
    register: { username: 'admin@algopharma.io', password: 'admin123' },
  },
  user: {
    login:    { username: 'viewer@example.com', password: 'viewer123' },
    register: { username: 'viewer@algopharma.io', password: 'viewer123' },
  },
} as const;

type RoleKey = keyof typeof PRESETS;

export function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [role, setRole] = useState<RoleKey>('admin');
  const [username, setUsername] = useState(PRESETS.admin.login.username);
  const [password, setPassword] = useState(PRESETS.admin.login.password);
  const { login, register, loading, error } = useAlgoPharmaAPI();
  const navigate = useNavigate();

  useEffect(() => {
    const preset = PRESETS[role][mode];
    setUsername(preset.username);
    setPassword(preset.password);
  }, [role, mode]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (mode === 'login') {
      const result = await login(username, password);
      if (result) navigate('/chat');
    } else {
      const result = await register(username, password, role);
      if (result) {
        const loginResult = await login(username, password);
        if (loginResult) navigate('/chat');
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden bg-[#060a14]">

      {/* ── Dark Checkerboard Background ── */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `
          linear-gradient(45deg, rgba(255,255,255,0.012) 25%, transparent 25%),
          linear-gradient(-45deg, rgba(255,255,255,0.012) 25%, transparent 25%),
          linear-gradient(45deg, transparent 75%, rgba(255,255,255,0.012) 75%),
          linear-gradient(-45deg, transparent 75%, rgba(255,255,255,0.012) 75%)
        `,
        backgroundSize: '40px 40px',
        backgroundPosition: '0 0, 0 20px, 20px -20px, -20px 0px',
      }} />

      {/* ── Glow Orbs ── */}
      <div className="absolute top-1/3 left-1/4 w-[420px] h-[420px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[380px] h-[380px] bg-indigo-500/10 rounded-full blur-[130px] pointer-events-none" />

      {/* ── Top Navbar with Role Toggle ── */}
      <nav className="sticky top-0 z-30 w-full flex items-center justify-between px-6 py-3.5 border-b border-white/[0.04] bg-[#060a14]/80 backdrop-blur-xl">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 bg-gradient-to-br from-cyan-400 to-indigo-500 rounded-lg flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <span className="text-white font-bold text-sm tracking-tight">AlgoPharma</span>
        </div>

        {/* Role Toggle Pill */}
        <div className="flex items-center gap-0.5 p-0.5 bg-zinc-900/80 border border-white/[0.06] rounded-full">
          {(['admin', 'user'] as const).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
                role === r
                  ? r === 'admin'
                    ? 'bg-gradient-to-r from-cyan-500/25 to-indigo-500/25 text-cyan-300 shadow-[0_0_12px_rgba(6,182,212,0.15)] border border-cyan-500/30'
                    : 'bg-white/[0.08] text-slate-200 border border-white/10'
                  : 'text-slate-600 hover:text-slate-400'
              }`}
            >
              {r === 'admin' ? <ShieldCheck className="w-3.5 h-3.5" /> : <UserCircle className="w-3.5 h-3.5" />}
              {r === 'admin' ? 'Admin' : 'User'}
            </button>
          ))}
        </div>

        <div className="w-20" /> {/* spacer for balance */}
      </nav>

      {/* ── Center Card ── */}
      <div className="flex-1 flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
          className="w-full max-w-[400px] relative z-10"
        >
          <div className="bg-zinc-900/50 backdrop-blur-xl border border-white/[0.07] rounded-2xl shadow-2xl shadow-black/40 p-7">

            {/* Header */}
            <div className="flex flex-col items-center mb-6">
              <h1 className="text-xl font-bold text-white tracking-tight">
                {mode === 'login' ? 'Welcome back' : 'Create account'}
              </h1>
              <p className="text-slate-500 text-xs mt-1">
                {mode === 'login' ? 'Access pharmacovigilance intelligence' : `Register as ${role}`}
              </p>
            </div>

            {/* Login / Register Toggle */}
            <div className="flex items-center gap-0.5 p-0.5 bg-zinc-800/50 border border-white/[0.04] rounded-lg mb-5">
              {(['login', 'register'] as const).map((m) => (
                <button
                  key={m}
                  type="button"
                  onClick={() => setMode(m)}
                  className={`flex-1 py-2 rounded-md text-[11px] font-medium tracking-wide uppercase transition-all duration-200 ${
                    mode === m
                      ? 'bg-white/[0.06] text-slate-200 border border-white/10'
                      : 'text-slate-600 hover:text-slate-400'
                  }`}
                >
                  {m === 'login' ? 'Sign In' : 'Register'}
                </button>
              ))}
            </div>

            {/* Error */}
            <AnimatePresence>
              {error && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-red-400 text-xs mb-4 overflow-hidden"
                >
                  {error}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-3.5">
              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Mail className="w-4 h-4 text-slate-600 group-focus-within:text-cyan-400 transition-colors" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-zinc-800/40 border border-white/[0.06] rounded-lg py-2.5 pl-10 pr-4 text-white text-sm placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-500/20 transition-all"
                  placeholder="Email address"
                  required
                />
              </div>

              <div className="relative group">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
                  <Lock className="w-4 h-4 text-slate-600 group-focus-within:text-cyan-400 transition-colors" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-zinc-800/40 border border-white/[0.06] rounded-lg py-2.5 pl-10 pr-4 text-white text-sm placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/30 focus:border-cyan-500/20 transition-all"
                  placeholder="Password"
                  required
                />
              </div>

              {/* POC Hint */}
              <div className="flex items-center gap-2 px-2.5 py-1.5 bg-cyan-500/[0.03] border border-cyan-500/10 rounded-md">
                <div className="w-1 h-1 rounded-full bg-cyan-400 shrink-0" />
                <span className="text-[10px] text-cyan-500/60 font-medium">
                  Pre-filled for POC — {role === 'admin' ? 'Admin' : 'Viewer'}
                </span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-400 hover:to-indigo-400 text-white font-semibold rounded-lg py-2.5 flex items-center justify-center gap-2 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-cyan-500/10 text-sm"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <>
                    {mode === 'login' ? 'Access Intelligence' : 'Register & Access'}
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </form>
          </div>

          <p className="text-center text-[10px] text-slate-700 mt-4">
            Pharmacovigilance Intelligence Platform · POC
          </p>
        </motion.div>
      </div>
    </div>
  );
}
