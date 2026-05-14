import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router';
import { motion, AnimatePresence } from 'motion/react';
import { Send, Activity, ShieldAlert, Bot, User, Loader2 } from 'lucide-react';
import { useAlgoPharmaAPI } from '../hooks/useAlgoPharmaAPI';

interface Message {
  id: string;
  type: 'user' | 'bot';
  content: string;
}

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Welcome to AlgoPharma Intelligence. Enter a drug name, symptom, or platform to begin adverse event surveillance.',
    }
  ]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { sendChat, loading, error, isAuthenticated } = useAlgoPharmaAPI();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
    } else {
      // Clear previous session's chat state on mount
      localStorage.removeItem('chat_state');
    }
  }, [isAuthenticated, navigate]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message to UI
    setMessages(prev => [...prev, { id: Date.now().toString(), type: 'user', content: userMessage }]);
    
    // Send to backend
    const result = await sendChat(userMessage);
    
    if (result) {
      setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', content: result.bot_message }]);
      
      if (result.ready && result.project_id) {
        // Wait a moment so user can read it, then transition to processing
        setTimeout(() => {
          navigate('/processing', { state: { projectId: result.project_id } });
        }, 1500);
      }
    } else if (error) {
      setMessages(prev => [...prev, { id: Date.now().toString(), type: 'bot', content: `Error: ${error}` }]);
    }
  };

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Decorative Background */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-indigo-500/10 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="glass-panel-subtle sticky top-0 z-20 flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-400 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">AlgoPharma</h1>
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-slate-400 font-medium">System Online</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          <div className="px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 text-cyan-400" />
            <span className="text-xs text-cyan-400 font-medium tracking-wide">PHARMACOVIGILANCE MODE</span>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 md:p-8 z-10 space-y-6">
        <div className="max-w-4xl mx-auto space-y-6">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                className={`flex gap-4 ${msg.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 shadow-lg ${
                  msg.type === 'user' 
                    ? 'bg-zinc-800 border border-white/10 text-slate-300' 
                    : 'bg-gradient-to-br from-cyan-500 to-indigo-500 text-white'
                }`}>
                  {msg.type === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
                </div>
                
                <div className={`max-w-[80%] rounded-2xl px-6 py-4 shadow-xl backdrop-blur-md ${
                  msg.type === 'user'
                    ? 'bg-zinc-800/80 border border-white/5 text-slate-200 rounded-tr-sm'
                    : 'bg-zinc-900/60 border border-cyan-500/20 text-slate-200 rounded-tl-sm'
                }`}>
                  <p className="leading-relaxed">{msg.content}</p>
                </div>
              </motion.div>
            ))}
            
            {loading && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-4"
              >
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-indigo-500 text-white flex items-center justify-center shrink-0 shadow-lg">
                  <Bot className="w-5 h-5" />
                </div>
                <div className="bg-zinc-900/60 border border-cyan-500/20 rounded-2xl rounded-tl-sm px-6 py-4 flex items-center gap-2">
                  <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
                  <span className="text-slate-400 text-sm">Analyzing intelligence...</span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <footer className="glass-panel-subtle sticky bottom-0 z-20 border-t border-white/5 p-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. Find adverse events for Aspirin on Reddit..."
              className="w-full bg-zinc-900/50 border border-white/10 rounded-2xl py-4 pl-6 pr-16 text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 transition-all shadow-inner"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="absolute right-2 top-2 bottom-2 w-12 flex items-center justify-center bg-cyan-500 hover:bg-cyan-400 text-zinc-950 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
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
  );
}
