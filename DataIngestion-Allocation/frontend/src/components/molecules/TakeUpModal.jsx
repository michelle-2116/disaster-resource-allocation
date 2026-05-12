import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../../services/api';

export function TakeUpModal({ needCard, incidentName, onClose, onSuccess }) {
  const [step, setStep] = useState('form'); // 'form' | 'submitting' | 'confirmed'
  const [formData, setFormData] = useState({ name: '', phone: '', email: '', note: '' });
  const [errors, setErrors] = useState({});
  const [reference, setReference] = useState('');

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!/^\d{10}$/.test(formData.phone.replace(/\D/g, ''))) newErrors.phone = 'Enter a valid 10-digit phone number';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) newErrors.email = 'Enter a valid email address';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setStep('submitting');
    
    const res = await api.takeUpNeedCard(
      needCard.id,
      formData.name,
      formData.phone,
      formData.email
    );

    if (!res.error) {
      const ref = `ReliefGrid-${Math.floor(100000 + Math.random() * 900000)}`;
      setReference(ref);
      setStep('confirmed');
      
      if (onSuccess) {
        onSuccess({ ...needCard, done_by: formData.name });
      }
    } else {
      // In a real app, handle error state here
      console.error(res.error);
      setStep('form');
    }
  };

  const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 }
  };

  const modalVariants = {
    hidden: { opacity: 0, y: 50, scale: 0.95 },
    visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring', damping: 25, stiffness: 300 } },
    exit: { opacity: 0, y: 20, scale: 0.95 }
  };

  return (
    <AnimatePresence>
      <motion.div 
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        variants={backdropVariants}
        initial="hidden"
        animate="visible"
        exit="hidden"
        onClick={onClose}
      >
        <motion.div 
          className="bg-bg-card w-full max-w-lg rounded-lg shadow-xl overflow-hidden flex flex-col max-h-[90vh]"
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex justify-between items-center px-6 py-4 border-b border-border bg-bg-primary">
            <h2 className="text-xl font-bold tracking-tight text-text-primary">
              {step === 'form' && 'Take Up This Need'}
              {step === 'submitting' && 'Processing...'}
              {step === 'confirmed' && 'Action Confirmed'}
            </h2>
            <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
              <X size={20} />
            </button>
          </div>

          <div className="overflow-y-auto p-6">
            {step === 'form' && (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="bg-bg-secondary border border-border p-3 rounded flex items-center justify-between mb-2">
                  <div>
                    <div className="text-xs text-text-secondary uppercase font-bold tracking-wider mb-0.5">Task</div>
                    <div className="font-serif font-bold text-lg">{needCard.quantity} × {needCard.item}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-text-secondary uppercase font-bold tracking-wider mb-0.5">Incident</div>
                    <div className="text-sm font-medium">{incidentName}</div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold mb-1.5">Full Name <span className="text-accent-red">*</span></label>
                  <input 
                    type="text" 
                    value={formData.name} 
                    onChange={e => setFormData({...formData, name: e.target.value})}
                    className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 ${errors.name ? 'border-accent-red focus:ring-accent-red/20' : 'border-border focus:border-accent-blue focus:ring-accent-blue/20 bg-bg-primary'}`}
                  />
                  {errors.name && <p className="text-accent-red text-xs mt-1 font-bold">{errors.name}</p>}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-bold mb-1.5">Phone <span className="text-accent-red">*</span></label>
                    <input 
                      type="tel" 
                      placeholder="10-digit number"
                      value={formData.phone} 
                      onChange={e => setFormData({...formData, phone: e.target.value})}
                      className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 ${errors.phone ? 'border-accent-red focus:ring-accent-red/20' : 'border-border focus:border-accent-blue focus:ring-accent-blue/20 bg-bg-primary'}`}
                    />
                    {errors.phone && <p className="text-accent-red text-xs mt-1 font-bold">{errors.phone}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-1.5">Email <span className="text-accent-red">*</span></label>
                    <input 
                      type="email" 
                      value={formData.email} 
                      onChange={e => setFormData({...formData, email: e.target.value})}
                      className={`w-full px-3 py-2 border rounded focus:outline-none focus:ring-2 ${errors.email ? 'border-accent-red focus:ring-accent-red/20' : 'border-border focus:border-accent-blue focus:ring-accent-blue/20 bg-bg-primary'}`}
                    />
                    {errors.email && <p className="text-accent-red text-xs mt-1 font-bold">{errors.email}</p>}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold mb-1.5 text-text-secondary">Brief note (optional)</label>
                  <textarea 
                    rows="2"
                    placeholder="Anything the coordination team should know?"
                    value={formData.note} 
                    onChange={e => setFormData({...formData, note: e.target.value})}
                    className="w-full px-3 py-2 border border-border bg-bg-primary rounded focus:outline-none focus:border-accent-blue focus:ring-2 focus:ring-accent-blue/20 resize-none"
                  ></textarea>
                </div>

                <button 
                  type="submit" 
                  className="w-full py-3 mt-4 bg-accent-red text-white font-bold rounded shadow-sm hover:bg-red-700 transition-colors"
                >
                  Confirm — I'll Handle This
                </button>
              </form>
            )}

            {step === 'submitting' && (
              <div className="py-12 flex flex-col items-center justify-center text-center">
                <Loader2 size={48} className="text-accent-blue animate-spin mb-4" />
                <h3 className="text-lg font-bold text-text-primary">Registering you for this task...</h3>
                <p className="text-text-secondary text-sm mt-2">Please do not close this window.</p>
              </div>
            )}

            {step === 'confirmed' && (
              <div className="py-6 flex flex-col items-center text-center">
                <motion.div 
                  initial={{ scale: 0 }} 
                  animate={{ scale: 1 }} 
                  transition={{ type: 'spring', stiffness: 200, damping: 15 }}
                  className="w-16 h-16 bg-accent-green/10 text-accent-green rounded-full flex items-center justify-center mb-4"
                >
                  <CheckCircle size={32} strokeWidth={2.5} />
                </motion.div>
                
                <h3 className="text-2xl font-bold text-text-primary mb-2">You're registered!</h3>
                <p className="text-text-secondary mb-6">The coordination team will reach you within 2 hours to confirm logistics.</p>

                <div className="w-full bg-bg-secondary border border-border rounded p-4 text-left space-y-3 mb-6">
                  <div className="flex justify-between border-b border-border pb-2">
                    <span className="text-sm font-bold text-text-secondary">Task:</span>
                    <span className="font-serif font-bold text-lg">{needCard.quantity} × {needCard.item}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-2">
                    <span className="text-sm font-bold text-text-secondary">For:</span>
                    <span className="text-sm font-medium">{incidentName}</span>
                  </div>
                  <div className="flex justify-between border-b border-border pb-2">
                    <span className="text-sm font-bold text-text-secondary">Contact:</span>
                    <span className="font-mono">{formData.phone}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-bold text-text-secondary">Reference:</span>
                    <span className="font-mono text-accent-blue font-bold">{reference}</span>
                  </div>
                </div>

                <button 
                  onClick={onClose}
                  className="w-full py-3 bg-text-primary text-white font-bold rounded shadow-sm hover:bg-gray-800 transition-colors"
                >
                  Close & Return to Dashboard
                </button>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
