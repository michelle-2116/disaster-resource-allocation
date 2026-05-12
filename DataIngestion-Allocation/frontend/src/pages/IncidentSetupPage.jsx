import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { AlertCircle, ArrowRight } from 'lucide-react';
import { saveIncident, getIncident } from '../services/api';
import { usePageTitle } from '../hooks/usePageTitle';

const EXAMPLE_INCIDENTS = [
  "Kerala Floods 2026",
  "Earthquake Himachal Pradesh 2026",
  "Cyclone Remal — Odisha Coast 2026",
  "Heatwave Nagpur — Maharashtra 2026",
  "Bridge Collapse NH44 — Himachal Pradesh 2026",
  "Disease Outbreak Hanta Virus — Bihar 2026"
];

export default function IncidentSetupPage() {
  usePageTitle('Select Incident');
  const navigate = useNavigate();
  
  const [incidentName, setIncidentName] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    // If incident already exists, redirect to dashboard
    const existing = getIncident();
    if (existing) {
      navigate('/');
    }
  }, [navigate]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!incidentName.trim()) {
      setError('Please enter an incident name');
      return;
    }
    
    if (incidentName.trim().length < 5) {
      setError('Incident name must be at least 5 characters');
      return;
    }

    // Save incident and navigate
    saveIncident(incidentName.trim());
    navigate('/');
  };

  const handleSelectExample = (example) => {
    setIncidentName(example);
    setError('');
  };

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-2xl"
      >
        {/* Header */}
        <div className="text-center mb-12">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200, damping: 15 }}
            className="w-16 h-16 bg-accent-red/10 text-accent-red rounded-full flex items-center justify-center mx-auto mb-6"
          >
            <AlertCircle size={32} strokeWidth={2} />
          </motion.div>
          
          <h1 className="text-4xl font-bold tracking-tight text-text-primary mb-3">
            Disaster Relief Dashboard
          </h1>
          <p className="text-lg text-text-secondary">
            Select or enter an incident to begin tracking and resource allocation
          </p>
        </div>

        {/* Form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="bg-bg-card border border-border rounded-lg p-8 mb-8 shadow-lg"
        >
          <label className="block text-sm font-bold text-text-secondary uppercase tracking-wider mb-3">
            Incident Name
          </label>
          
          <input
            type="text"
            value={incidentName}
            onChange={(e) => {
              setIncidentName(e.target.value);
              if (error) setError('');
            }}
            placeholder="e.g., Kerala Floods 2026"
            className={`w-full px-4 py-3 bg-bg-primary border-2 rounded-lg text-text-primary font-bold text-lg placeholder:text-text-muted focus:outline-none transition-colors ${
              error ? 'border-accent-red focus:border-accent-red' : 'border-border focus:border-accent-blue'
            }`}
            autoFocus
          />
          
          {error && (
            <motion.p
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-accent-red font-bold text-sm mt-2"
            >
              {error}
            </motion.p>
          )}

          <button
            type="submit"
            className="w-full mt-6 py-4 bg-accent-red text-white font-bold text-lg rounded-lg shadow-md hover:bg-red-700 transition-colors flex items-center justify-center gap-2 group"
          >
            Start Tracking
            <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
          </button>
        </motion.form>

        {/* Examples */}
        <div>
          <p className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-4">
            Or select an example:
          </p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {EXAMPLE_INCIDENTS.map((example, index) => (
              <motion.button
                key={example}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 + index * 0.05 }}
                onClick={() => handleSelectExample(example)}
                className="px-4 py-3 bg-bg-secondary border border-border rounded-lg text-text-primary font-bold text-sm hover:border-accent-blue hover:bg-border transition-colors text-left"
              >
                {example}
              </motion.button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center text-xs text-text-muted mt-12"
        >
          You can change the incident later from the dashboard settings
        </motion.p>
      </motion.div>
    </div>
  );
}
