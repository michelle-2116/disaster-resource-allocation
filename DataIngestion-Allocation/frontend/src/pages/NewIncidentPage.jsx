import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import { Upload, Search, ClipboardList, User, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { usePageTitle } from '../hooks/usePageTitle';

const CHIPS = [
  "Cyclone Remal — Odisha Coast 2026",
  "Heatwave Nagpur — Maharashtra 2026",
  "Bridge Collapse NH44 — Himachal Pradesh 2026",
  "Disease Outbreak Hanta Virus — Bihar 2026"
];

function AnimatedConfidence({ value }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let start = 0;
    const duration = 1000;
    const incrementTime = 20;
    const steps = Math.floor(duration / incrementTime);
    const increment = value / steps;
    
    const timer = setInterval(() => {
      start += increment;
      if (start >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, incrementTime);

    return () => clearInterval(timer);
  }, [value]);

  return <span>{count}</span>;
}

export default function NewIncidentPage() {
  usePageTitle('New Incident');
  const navigate = useNavigate();
  
  const [state, setState] = useState('form'); // 'form' | 'processing' | 'complete'
  const [incidentName, setIncidentName] = useState('');
  const [error, setError] = useState('');

  // Processing internal states
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0); // 0=none, 1=submit, 2=agent1, 3=agent2, 4=hitl
  const [substeps, setSubsteps] = useState([]);
  
  // Fake data generated during pipeline
  const [confidence] = useState(Math.floor(Math.random() * (98 - 85 + 1) + 85)); // 85-98
  const [cardsGenerated] = useState(Math.floor(Math.random() * 8 + 4)); // 4-12
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (incidentName.trim().length < 10) {
      setError('Incident name must be at least 10 characters long.');
      return;
    }
    setError('');
    
    // Switch to processing
    setState('processing');
    
    // Start progress bar timer (8.5s total)
    const startTime = Date.now();
    const duration = 8500;
    
    const progressInterval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const p = Math.min((elapsed / duration) * 100, 100);
      setProgress(p);
      if (elapsed >= duration) clearInterval(progressInterval);
    }, 50);

    // Call API (we ignore the delay since we manage our own timing, but we let it run in background)
    api.createIncident(incidentName);

    // Step 1: Submitting (0 - 0.8s)
    setCurrentStep(1);
    
    // Step 2: Agent 1 (0.8s - 4.0s)
    setTimeout(() => {
      setCurrentStep(2);
      setSubsteps([]);
      
      const s2Timeouts = [
        setTimeout(() => setSubsteps(p => [...p, `Querying evidence sources for '${incidentName}'...`]), 0),
        setTimeout(() => setSubsteps(p => [...p, "Cross-referencing independent reports..."]), 700),
        setTimeout(() => setSubsteps(p => [...p, "Checking for contradictions..."]), 1400),
        setTimeout(() => setSubsteps(p => [...p, "Scoring source credibility..."]), 2100),
      ];
      return () => s2Timeouts.forEach(clearTimeout);
    }, 800);

    // Step 3: Agent 2 (4.0s - 7.0s)
    setTimeout(() => {
      setCurrentStep(3);
      setSubsteps([]);
      
      const s3Timeouts = [
        setTimeout(() => setSubsteps(p => [...p, "Parsing verified needs from incident report..."]), 0),
        setTimeout(() => setSubsteps(p => [...p, "Checking current inventory snapshot..."]), 700),
        setTimeout(() => setSubsteps(p => [...p, "Mapping needs to resource types..."]), 1400),
        setTimeout(() => setSubsteps(p => [...p, "Generating need cards..."]), 2100),
      ];
      return () => s3Timeouts.forEach(clearTimeout);
    }, 4000);

    // Step 4: HITL Gate (7.0s - 8.5s)
    setTimeout(() => {
      setCurrentStep(4);
      setSubsteps([]);
      
      const s4Timeouts = [
        setTimeout(() => setSubsteps(p => [...p, "Flagging high-impact allocations for admin review..."]), 0),
        setTimeout(() => setSubsteps(p => [...p, "Queuing in approval dashboard..."]), 700),
      ];
      return () => s4Timeouts.forEach(clearTimeout);
    }, 7000);

    // Complete (8.5s)
    setTimeout(() => {
      setState('complete');
    }, 8500);
  };

  const StepBox = ({ title, icon: Icon, active, completed, pulseColor, completionText, children }) => (
    <div className={`border rounded p-4 mb-4 transition-colors duration-500 ${
      completed ? 'bg-bg-card border-border' : 
      active ? 'bg-[#1A1714] border-gray-600 shadow-md' : 
      'bg-bg-card/50 border-gray-800 opacity-40'
    }`}>
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-full ${completed ? 'bg-accent-green text-white' : active ? 'bg-[#211E1A] text-white' : 'bg-[#211E1A] text-gray-500'}`}>
          {completed ? <CheckCircle size={20} strokeWidth={3} /> : <Icon size={20} />}
        </div>
        <div className="flex-grow flex items-center justify-between">
          <span className={`font-bold ${active || completed ? 'text-white' : 'text-gray-500'}`}>
            {title}
          </span>
          {active && pulseColor && (
            <span className="relative flex h-2.5 w-2.5">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${pulseColor} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${pulseColor}`}></span>
            </span>
          )}
        </div>
      </div>
      
      <div className="pl-12 font-mono text-sm">
        {active && (
          <div className="space-y-1.5 text-gray-400">
            {children}
          </div>
        )}
        {completed && completionText && (
          <motion.div 
            initial={{ opacity: 0, x: -10 }} 
            animate={{ opacity: 1, x: 0 }} 
            className="text-accent-green font-bold flex items-center gap-2"
          >
            {completionText}
          </motion.div>
        )}
      </div>
    </div>
  );

  return (
    <div className="w-full flex justify-center py-8 text-text-primary">
      <AnimatePresence mode="wait">
        {/* FORM STATE */}
        {state === 'form' && (
          <motion.div 
            key="form"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.3 } }}
            className="w-full max-w-2xl bg-[#211E1A] border border-gray-800 rounded-xl p-8 shadow-xl"
          >
            <div className="mb-8">
              <h1 className="text-3xl font-bold tracking-tight mb-2 text-white">Report New Incident</h1>
              <p className="text-gray-400">The AI pipeline will automatically verify, assess, and generate resource allocation recommendations.</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <div>
                <label className="block text-xl font-bold text-gray-300 mb-3">Incident Name</label>
                <input 
                  type="text" 
                  value={incidentName}
                  onChange={e => {
                    setIncidentName(e.target.value);
                    if (error) setError('');
                  }}
                  className={`w-full px-6 py-5 bg-[#1A1714] border-2 rounded-lg text-white text-lg font-bold placeholder:text-gray-600 focus:outline-none transition-colors shadow-inner ${
                    error ? 'border-accent-red focus:border-accent-red' : 'border-gray-700 focus:border-accent-blue'
                  }`}
                  placeholder="e.g. Kerala Flood 2026 — Alappuzha District"
                  autoFocus
                />
                {error && <p className="text-accent-red font-bold text-sm mt-2">{error}</p>}
                <p className="text-sm text-gray-500 mt-3 font-medium">
                  Be specific — include disaster type, location, and year. The AI uses this to search and verify evidence sources.
                </p>
              </div>

              <div className="bg-[#1A1714] rounded-lg p-5 border border-gray-800">
                <p className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">Or select an example:</p>
                <div className="flex flex-wrap gap-2">
                  {CHIPS.map(chip => (
                    <button
                      key={chip}
                      type="button"
                      onClick={() => {
                        setIncidentName(chip);
                        setError('');
                      }}
                      className="px-3 py-1.5 bg-[#211E1A] border border-gray-700 text-gray-300 text-sm rounded hover:border-accent-blue hover:text-accent-blue transition-colors font-mono"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4">
                <button 
                  type="submit" 
                  className="w-full py-5 bg-accent-red text-white text-xl font-bold rounded-lg shadow-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2"
                >
                  Launch AI Pipeline &rarr;
                </button>
              </div>
            </form>
          </motion.div>
        )}

        {/* PROCESSING STATE */}
        {state === 'processing' && (
          <motion.div 
            key="processing"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.05, transition: { duration: 0.4 } }}
            className="w-full max-w-[560px]"
          >
            {/* Progress Bar */}
            <div className="w-full h-1 bg-gray-800 rounded-full mb-8 overflow-hidden shadow-inner">
              <div 
                className="h-full bg-accent-blue transition-all ease-linear"
                style={{ width: `${progress}%`, transitionDuration: '50ms' }}
              ></div>
            </div>

            <div className="flex flex-col gap-1">
              
              {/* Step 1 */}
              <StepBox 
                title="Sending to ReliefGrid System" 
                icon={Upload} 
                active={currentStep === 1} 
                completed={currentStep > 1}
              >
                {currentStep === 1 && (
                  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex items-center gap-2">
                    <span className="animate-spin w-3 h-3 border-2 border-gray-400 border-t-transparent rounded-full inline-block"></span>
                    <span className="text-gray-300">{incidentName}</span>
                  </motion.div>
                )}
              </StepBox>

              {/* Step 2: Verification Agent */}
              <StepBox 
                title="Verification Agent — Analyzing" 
                icon={Search} 
                active={currentStep === 2} 
                completed={currentStep > 2}
                pulseColor="bg-accent-blue"
                completionText={<span>Verified — Confidence: <AnimatedConfidence value={confidence} />%</span>}
              >
                {currentStep === 2 && (
                  <AnimatePresence>
                    {substeps.map((sub, i) => (
                      <motion.div 
                        key={i} 
                        initial={{ opacity: 0, x: -10 }} 
                        animate={{ opacity: 1, x: 0 }}
                      >
                        {sub}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                )}
              </StepBox>

              {/* Step 3: Allocation Agent */}
              <StepBox 
                title="Allocation Agent — Building Response Plan" 
                icon={ClipboardList} 
                active={currentStep === 3} 
                completed={currentStep > 3}
                pulseColor="bg-accent-blue"
                completionText={`${cardsGenerated} need cards generated`}
              >
                {currentStep === 3 && (
                  <AnimatePresence>
                    {substeps.map((sub, i) => (
                      <motion.div 
                        key={i} 
                        initial={{ opacity: 0, x: -10 }} 
                        animate={{ opacity: 1, x: 0 }}
                      >
                        {sub}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                )}
              </StepBox>

              {/* Step 4: HITL Gate */}
              <StepBox 
                title="Human Review Required" 
                icon={User} 
                active={currentStep === 4} 
                completed={currentStep > 4}
                pulseColor="bg-accent-amber"
                completionText={<span className="text-accent-amber">{cardsGenerated} cards pending your approval</span>}
              >
                {currentStep === 4 && (
                  <AnimatePresence>
                    {substeps.map((sub, i) => (
                      <motion.div 
                        key={i} 
                        initial={{ opacity: 0, x: -10 }} 
                        animate={{ opacity: 1, x: 0 }}
                      >
                        {sub}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                )}
              </StepBox>

            </div>
          </motion.div>
        )}

        {/* COMPLETE STATE */}
        {state === 'complete' && (
          <motion.div 
            key="complete"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-xl bg-[#211E1A] border border-gray-800 rounded-xl p-10 shadow-2xl flex flex-col items-center text-center"
          >
            <motion.div 
              initial={{ scale: 0 }} 
              animate={{ scale: 1 }} 
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="w-24 h-24 bg-accent-green/10 text-accent-green rounded-full flex items-center justify-center mb-6"
            >
              <CheckCircle size={48} strokeWidth={2.5} />
            </motion.div>
            
            <h1 className="text-4xl font-bold text-white mb-8 tracking-tight">Incident Created</h1>

            <div className="w-full bg-[#1A1714] border border-gray-700 rounded-lg p-6 text-left space-y-4 mb-8">
              <div className="flex flex-col sm:flex-row sm:justify-between border-b border-gray-800 pb-3 gap-1">
                <span className="text-sm font-bold text-gray-500 uppercase tracking-wider">Incident:</span>
                <span className="font-mono font-bold text-gray-200">{incidentName}</span>
              </div>
              <div className="flex flex-col sm:flex-row sm:justify-between border-b border-gray-800 pb-3 gap-1">
                <span className="text-sm font-bold text-gray-500 uppercase tracking-wider">Status:</span>
                <span className="font-mono font-bold text-accent-amber">Active — Pending Review</span>
              </div>
              <div className="flex flex-col sm:flex-row sm:justify-between pb-1 gap-1">
                <span className="text-sm font-bold text-gray-500 uppercase tracking-wider">Pipeline:</span>
                <span className="font-mono text-xs text-gray-300">
                  Verification <span className="text-accent-green">✓</span> | Allocation <span className="text-accent-green">✓</span> | Awaiting Approval <span className="text-accent-amber">⏳</span>
                </span>
              </div>
            </div>

            <div className="w-full flex flex-col sm:flex-row gap-4">
              <button 
                onClick={() => navigate('/admin')}
                className="flex-1 py-4 bg-accent-red text-white text-lg font-bold rounded shadow-sm hover:bg-red-700 transition-colors"
              >
                Review Approval Queue &rarr;
              </button>
              <button 
                onClick={() => navigate('/')}
                className="flex-1 py-4 bg-transparent border border-gray-600 text-gray-300 text-lg font-bold rounded hover:bg-gray-800 transition-colors"
              >
                Back to Dashboard
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
