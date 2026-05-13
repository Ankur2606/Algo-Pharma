import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router';
import { motion } from 'motion/react';
import { CheckCircle2, Loader2, Database, Shield, Brain, Activity, LineChart, Globe } from 'lucide-react';

const STEPS = [
  { id: 1, name: 'Firecrawl Target Selection', icon: Globe },
  { id: 2, name: 'Web Scraping & Ingestion', icon: Database },
  { id: 3, name: 'PII Redaction & De-identification', icon: Shield },
  { id: 4, name: 'NLP Entity Extraction (NER)', icon: Brain },
  { id: 5, name: 'Signal Detection Engine', icon: Activity },
  { id: 6, name: 'Aggregating Intelligence', icon: LineChart },
];

export function ProcessingPage() {
  const [currentStep, setCurrentStep] = useState(1);
  const navigate = useNavigate();
  const location = useLocation();
  const projectId = location.state?.projectId;

  useEffect(() => {
    if (!projectId) {
      navigate('/chat');
      return;
    }

    // Simulate the step progression (approx 1.5s per step)
    const interval = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= STEPS.length) {
          clearInterval(interval);
          setTimeout(() => {
            navigate('/dashboard', { state: { projectId } });
          }, 500);
          return prev;
        }
        return prev + 1;
      });
    }, 1500);

    return () => clearInterval(interval);
  }, [projectId, navigate]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden p-6">
      {/* Decorative */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="text-center mb-12 relative z-10">
        <h1 className="text-4xl font-bold text-white mb-4">Initializing Intelligence Engine</h1>
        <p className="text-slate-400">Deploying asynchronous workers to process pharmacovigilance data</p>
      </div>

      <div className="w-full max-w-2xl relative z-10">
        <div className="glass-panel p-8 rounded-3xl space-y-6 relative overflow-hidden">
          
          {/* Animated progress bar background */}
          <div className="absolute top-0 left-0 h-1 bg-cyan-500/20 w-full" />
          <motion.div 
            className="absolute top-0 left-0 h-1 bg-gradient-to-r from-cyan-400 to-indigo-500"
            initial={{ width: '0%' }}
            animate={{ width: `${(currentStep / STEPS.length) * 100}%` }}
            transition={{ duration: 0.5 }}
          />

          {STEPS.map((step) => {
            const Icon = step.icon;
            const isCompleted = currentStep > step.id;
            const isCurrent = currentStep === step.id;
            const isPending = currentStep < step.id;

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ 
                  opacity: isPending ? 0.4 : 1,
                  x: 0,
                  scale: isCurrent ? 1.02 : 1
                }}
                className={`flex items-center gap-4 p-4 rounded-2xl transition-all ${
                  isCurrent ? 'bg-cyan-500/10 border border-cyan-500/30 shadow-[0_0_20px_rgba(6,182,212,0.1)]' : 'bg-zinc-900/40 border border-white/5'
                }`}
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                  isCompleted ? 'bg-emerald-500/20 text-emerald-400' :
                  isCurrent ? 'bg-cyan-500/20 text-cyan-400' :
                  'bg-zinc-800 text-slate-500'
                }`}>
                  {isCompleted ? <CheckCircle2 className="w-6 h-6" /> : 
                   isCurrent ? <Loader2 className="w-6 h-6 animate-spin" /> : 
                   <Icon className="w-6 h-6" />}
                </div>
                
                <div className="flex-1">
                  <h3 className={`font-semibold ${isCurrent ? 'text-white' : 'text-slate-300'}`}>
                    {step.name}
                  </h3>
                  <p className="text-sm text-slate-500">
                    {isCompleted ? 'Complete' : isCurrent ? 'Processing...' : 'Waiting...'}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
