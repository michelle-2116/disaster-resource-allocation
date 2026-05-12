import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';
import { INCIDENTS } from '../data/incidents';
import { NeedTypeBadge } from '../components/atoms/NeedTypeBadge';
import { usePageTitle } from '../hooks/usePageTitle';

export default function ContributePage() {
  usePageTitle('Contribute');
  const { needCardId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [allCards, setAllCards] = useState([]);
  const [selectedCard, setSelectedCard] = useState(null);
  const [incidentName, setIncidentName] = useState('');

  const [step, setStep] = useState('form'); // 'form' | 'confirming' | 'confirmed'
  const [checklistStep, setChecklistStep] = useState(0); // 0, 1, 2, 3

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    email: '',
    city: '',
    item: '',
    quantity: '',
    unit: 'units',
    canDeliver: 'No',
    deliveryAddress: '',
    notes: ''
  });
  const [errors, setErrors] = useState({});
  const [reference, setReference] = useState('');

  // Handle wrong mode redirect
  useEffect(() => {
    if (location.state?.mode === 'volunteer') {
      alert("Volunteering is now handled directly on the Dashboard.");
      navigate('/');
    }
  }, [location, navigate]);

  // Load Data
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const res = await api.getPublicNeedCards();
      if (res.data) {
        setAllCards(res.data);
        
        let card = res.data.find(c => c.id === needCardId);
        if (card) {
          setSelectedCard(card);
          setFormData(prev => ({ ...prev, item: card.item }));
          
          const inc = INCIDENTS.find(i => i.id === card.incident_id);
          if (inc) setIncidentName(`${inc.name} — ${inc.location}`);
        } else if (needCardId) {
          // invalid ID, clear it
          navigate('/contribute', { replace: true });
        }
      }
      setLoading(false);
    };
    loadData();
  }, [needCardId, navigate]);

  // Handle card selection from dropdown if no ID in URL
  const handleCardSelect = (e) => {
    const cardId = e.target.value;
    if (!cardId) {
      setSelectedCard(null);
      setIncidentName('');
      setFormData(prev => ({ ...prev, item: '' }));
      return;
    }
    const card = allCards.find(c => c.id === cardId);
    if (card) {
      setSelectedCard(card);
      setFormData(prev => ({ ...prev, item: card.item }));
      const inc = INCIDENTS.find(i => i.id === card.incident_id);
      if (inc) setIncidentName(`${inc.name} — ${inc.location}`);
      navigate(`/contribute/${card.id}`, { replace: true, state: { mode: 'donate' } });
    }
  };

  const validate = () => {
    const newErrors = {};
    if (!formData.name.trim()) newErrors.name = 'Name is required';
    if (!/^\d{10}$/.test(formData.phone.replace(/\D/g, ''))) newErrors.phone = 'Enter a valid 10-digit phone number';
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) newErrors.email = 'Enter a valid email address';
    if (!formData.city.trim()) newErrors.city = 'City is required';
    if (!formData.item.trim()) newErrors.item = 'Item is required';
    if (!formData.quantity || isNaN(formData.quantity) || Number(formData.quantity) <= 0) newErrors.quantity = 'Enter a valid quantity';
    if (formData.canDeliver === 'Yes' && !formData.deliveryAddress.trim()) newErrors.deliveryAddress = 'Delivery address is required';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate() || !selectedCard) return;

    setStep('confirming');
    setChecklistStep(0);

    // Timeline: 0.5s, 1.2s, 2.0s, 2.5s done
    setTimeout(() => setChecklistStep(1), 500);
    setTimeout(() => setChecklistStep(2), 1200);
    setTimeout(() => setChecklistStep(3), 2000);
    setTimeout(() => {
      setReference(`ReliefGrid-${Math.floor(100000 + Math.random() * 900000)}`);
      setStep('confirmed');
    }, 2500);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center bg-bg-primary text-text-primary">Loading...</div>;
  }

  return (
    <div className="bg-bg-primary min-h-screen py-12 px-6">
      <div className="max-w-3xl mx-auto">
        
        {/* Page Header */}
        <div className="mb-8 border-b border-border pb-6">
          <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-2">Resource Donation</h1>
          <p className="text-text-secondary">Pledge supplies and resources to active disaster incidents.</p>
        </div>

        {/* Dynamic State Rendering */}
        {step === 'form' && (
          <div className="bg-bg-card border border-border rounded shadow-sm overflow-hidden">
            
            {/* Top Context Strip */}
            {selectedCard ? (
              <div className="bg-bg-secondary p-5 border-b border-border">
                <p className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-3">Donating resources for:</p>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-3 mb-2">
                      <NeedTypeBadge type={selectedCard.tool_name} />
                      <span className="text-sm font-medium text-text-secondary">{incidentName}</span>
                    </div>
                    <h2 className="text-2xl font-bold font-serif text-text-primary">{selectedCard.item}</h2>
                  </div>
                  <div className="bg-bg-card border border-border px-4 py-2 rounded text-center">
                    <div className="text-xs font-bold text-text-secondary uppercase tracking-wider">Required</div>
                    <div className="text-xl font-mono font-bold text-accent-blue">{selectedCard.quantity}</div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-bg-secondary p-5 border-b border-border">
                <label className="block text-sm font-bold text-text-primary mb-2">Select a need to donate towards:</label>
                <select 
                  className="w-full px-4 py-3 bg-bg-card border border-border rounded focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
                  onChange={handleCardSelect}
                  defaultValue=""
                >
                  <option value="" disabled>-- Select an open need --</option>
                  {allCards.map(card => (
                    <option key={card.id} value={card.id}>
                      {card.quantity} × {card.item} (Incident: {INCIDENTS.find(i=>i.id === card.incident_id)?.name})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 md:p-8 space-y-8">
              
              <div className="space-y-6">
                <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider border-b border-border pb-2">Donor Details</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">Full Name <span className="text-accent-red">*</span></label>
                    <input 
                      type="text" 
                      value={formData.name}
                      onChange={e => setFormData({...formData, name: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded focus:outline-none focus:ring-1 ${errors.name ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                    />
                    {errors.name && <p className="text-accent-red text-xs mt-1 font-bold">{errors.name}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">Phone Number <span className="text-accent-red">*</span></label>
                    <input 
                      type="tel" 
                      placeholder="10 digits"
                      value={formData.phone}
                      onChange={e => setFormData({...formData, phone: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded focus:outline-none focus:ring-1 ${errors.phone ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                    />
                    {errors.phone && <p className="text-accent-red text-xs mt-1 font-bold">{errors.phone}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">Email <span className="text-accent-red">*</span></label>
                    <input 
                      type="email" 
                      value={formData.email}
                      onChange={e => setFormData({...formData, email: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded focus:outline-none focus:ring-1 ${errors.email ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                    />
                    {errors.email && <p className="text-accent-red text-xs mt-1 font-bold">{errors.email}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">City <span className="text-accent-red">*</span></label>
                    <input 
                      type="text" 
                      value={formData.city}
                      onChange={e => setFormData({...formData, city: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded focus:outline-none focus:ring-1 ${errors.city ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                    />
                    {errors.city && <p className="text-accent-red text-xs mt-1 font-bold">{errors.city}</p>}
                  </div>
                </div>
              </div>

              <div className="space-y-6">
                <h3 className="text-sm font-bold text-text-secondary uppercase tracking-wider border-b border-border pb-2">Donation Specs</h3>
                
                <div>
                  <label className="block text-sm font-bold mb-1.5 text-text-primary">Item to Donate <span className="text-accent-red">*</span></label>
                  <input 
                    type="text" 
                    value={formData.item}
                    onChange={e => setFormData({...formData, item: e.target.value})}
                    className={`w-full px-4 py-2 bg-bg-primary border rounded focus:outline-none focus:ring-1 ${errors.item ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                  />
                  {errors.item && <p className="text-accent-red text-xs mt-1 font-bold">{errors.item}</p>}
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <div className="flex justify-between items-end mb-1.5">
                      <label className="block text-sm font-bold text-text-primary">Quantity <span className="text-accent-red">*</span></label>
                      {selectedCard && <span className="text-xs text-text-secondary font-mono">Need: {selectedCard.quantity}</span>}
                    </div>
                    <input 
                      type="number" 
                      min="1"
                      value={formData.quantity}
                      onChange={e => setFormData({...formData, quantity: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded font-mono focus:outline-none focus:ring-1 ${errors.quantity ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`} 
                    />
                    {errors.quantity && <p className="text-accent-red text-xs mt-1 font-bold">{errors.quantity}</p>}
                  </div>
                  <div>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">Unit <span className="text-accent-red">*</span></label>
                    <select 
                      value={formData.unit}
                      onChange={e => setFormData({...formData, unit: e.target.value})}
                      className="w-full px-4 py-2 bg-bg-primary border border-border rounded focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
                    >
                      <option value="kg">kg</option>
                      <option value="liters">liters</option>
                      <option value="units">units</option>
                      <option value="packets">packets</option>
                      <option value="boxes">boxes</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-bold mb-3 text-text-primary">Can you drop this at a collection center?</label>
                  <div className="flex gap-6">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input 
                        type="radio" 
                        name="deliver" 
                        value="Yes" 
                        checked={formData.canDeliver === 'Yes'}
                        onChange={() => setFormData({...formData, canDeliver: 'Yes'})}
                        className="text-accent-blue focus:ring-accent-blue"
                      />
                      <span>Yes, I'll drop it off</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input 
                        type="radio" 
                        name="deliver" 
                        value="No" 
                        checked={formData.canDeliver === 'No'}
                        onChange={() => setFormData({...formData, canDeliver: 'No'})}
                        className="text-accent-blue focus:ring-accent-blue"
                      />
                      <span>No, please pick it up</span>
                    </label>
                  </div>
                </div>

                {formData.canDeliver === 'No' && (
                  <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
                    <label className="block text-sm font-bold mb-1.5 text-text-primary">Pickup Address <span className="text-accent-red">*</span></label>
                    <textarea 
                      rows="3" 
                      value={formData.deliveryAddress}
                      onChange={e => setFormData({...formData, deliveryAddress: e.target.value})}
                      className={`w-full px-4 py-2 bg-bg-primary border rounded resize-none focus:outline-none focus:ring-1 ${errors.deliveryAddress ? 'border-accent-red focus:ring-accent-red' : 'border-border focus:border-accent-blue focus:ring-accent-blue'}`}
                    ></textarea>
                    {errors.deliveryAddress && <p className="text-accent-red text-xs mt-1 font-bold">{errors.deliveryAddress}</p>}
                  </motion.div>
                )}

                <div>
                  <label className="block text-sm font-bold mb-1.5 text-text-primary">Additional Notes</label>
                  <textarea 
                    rows="2" 
                    value={formData.notes}
                    onChange={e => setFormData({...formData, notes: e.target.value})}
                    className="w-full px-4 py-2 bg-bg-primary border border-border rounded resize-none focus:outline-none focus:border-accent-blue focus:ring-1 focus:ring-accent-blue"
                  ></textarea>
                </div>
              </div>

              <div className="pt-6 border-t border-border">
                <button 
                  type="submit" 
                  disabled={!selectedCard}
                  className={`w-full py-4 font-bold text-lg rounded shadow-sm transition-colors ${selectedCard ? 'bg-text-primary text-white hover:bg-gray-800' : 'bg-gray-300 text-gray-500 cursor-not-allowed'}`}
                >
                  Submit Donation
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Confirming State */}
        {step === 'confirming' && (
          <div className="bg-bg-card border border-border rounded shadow-sm p-12 flex flex-col items-center justify-center min-h-[400px]">
            <Loader2 size={48} className="text-accent-blue animate-spin mb-6" />
            <h2 className="text-2xl font-bold text-text-primary mb-8">Registering your donation...</h2>
            
            <div className="space-y-4 w-full max-w-sm text-left">
              <div className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-colors ${checklistStep >= 1 ? 'bg-accent-green text-white' : 'bg-gray-200 text-transparent'}`}>
                  <CheckCircle size={14} strokeWidth={3} />
                </div>
                <span className={checklistStep >= 1 ? 'text-text-primary font-medium' : 'text-text-muted'}>Details received</span>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-colors ${checklistStep >= 2 ? 'bg-accent-green text-white' : 'bg-gray-200 text-transparent'}`}>
                  <CheckCircle size={14} strokeWidth={3} />
                </div>
                <span className={checklistStep >= 2 ? 'text-text-primary font-medium' : 'text-text-muted'}>Logging against need card <span className="font-mono text-xs">{selectedCard?.id}</span>...</span>
              </div>
              <div className="flex items-center gap-3">
                <div className={`w-5 h-5 rounded-full flex items-center justify-center transition-colors ${checklistStep >= 3 ? 'bg-accent-green text-white' : 'bg-gray-200 text-transparent'}`}>
                  <CheckCircle size={14} strokeWidth={3} />
                </div>
                <span className={checklistStep >= 3 ? 'text-text-primary font-medium' : 'text-text-muted'}>Notifying coordination team...</span>
              </div>
            </div>
          </div>
        )}

        {/* Confirmed State */}
        {step === 'confirmed' && (
          <div className="bg-bg-card border border-border rounded shadow-sm p-12 flex flex-col items-center text-center">
            <motion.div 
              initial={{ scale: 0 }} 
              animate={{ scale: 1 }} 
              transition={{ type: 'spring', stiffness: 200, damping: 15 }}
              className="w-20 h-20 bg-accent-green/10 text-accent-green rounded-full flex items-center justify-center mb-6"
            >
              <CheckCircle size={40} strokeWidth={2.5} />
            </motion.div>
            
            <h2 className="text-3xl font-bold text-text-primary mb-2">Donation Registered</h2>
            <p className="text-text-secondary mb-8 text-lg">Thank you for your contribution to the relief efforts.</p>

            <div className="w-full max-w-md bg-bg-secondary border border-border rounded p-6 text-left space-y-4 mb-8">
              <div className="flex justify-between border-b border-border pb-3">
                <span className="text-sm font-bold text-text-secondary">Item:</span>
                <span className="font-mono font-bold">{formData.item} — {formData.quantity} {formData.unit}</span>
              </div>
              <div className="flex justify-between border-b border-border pb-3">
                <span className="text-sm font-bold text-text-secondary">For:</span>
                <span className="text-sm font-medium">{incidentName}</span>
              </div>
              <div className="flex justify-between border-b border-border pb-3">
                <span className="text-sm font-bold text-text-secondary">Reference:</span>
                <span className="font-mono text-accent-blue font-bold">{reference}</span>
              </div>
              <p className="text-sm text-text-primary font-medium pt-1 text-center bg-accent-green/10 text-accent-green p-2 rounded">
                Coordination team will contact you at <span className="font-mono">{formData.phone}</span> within 2 hours.
              </p>
            </div>

            <Link 
              to="/"
              className="px-8 py-3 bg-transparent border border-border text-text-primary font-bold rounded hover:bg-bg-secondary transition-colors"
            >
              Back to Dashboard
            </Link>
          </div>
        )}

      </div>
    </div>
  );
}
