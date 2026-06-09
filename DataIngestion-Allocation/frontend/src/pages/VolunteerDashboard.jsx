import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { INCIDENTS } from '../data/incidents';
import { PublicNeedCard, TakeUpModal, Skeleton } from '../components';
import { usePageTitle } from '../hooks/usePageTitle';
import { useToast } from '../components/ToastProvider';
import { usePolling } from '../hooks/usePolling';
import { motion, AnimatePresence } from 'framer-motion';
import { ClipboardList, CheckCircle2, Heart } from 'lucide-react';

export default function VolunteerDashboard() {
  usePageTitle('Volunteer Dashboard');
  const showToast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [allCards, setAllCards] = useState([]);
  const [activeTab, setActiveTab] = useState('available'); // 'available' | 'commitments'
  const [selectedCard, setSelectedCard] = useState(null);
  const [volunteerName, setVolunteerName] = useState('');
  const [volunteerEmail, setVolunteerEmail] = useState('');
  const [volunteerPhone, setVolunteerPhone] = useState('');

  useEffect(() => {
    setVolunteerName(localStorage.getItem('volunteer_name') || 'Volunteer');
    setVolunteerEmail(localStorage.getItem('volunteer_email') || 'volunteer@reliefgrid.org');
    setVolunteerPhone(localStorage.getItem('volunteer_phone') || '9876543210');
  }, []);

  const loadData = async () => {
    try {
      const res = await api.getAllNeedCards();
      if (res.error) {
        showToast(`Error fetching need cards: ${res.error}`, 'error');
        return;
      }
      if (res.data) {
        setAllCards(res.data);
      }
      setLoading(false);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch data';
      showToast(errorMsg, 'error');
    }
  };

  // Poll for updates every 30 seconds
  const pollInterval = parseInt(import.meta.env.VITE_POLL_INTERVAL_MS || '30000');
  usePolling(loadData, pollInterval, true);

  useEffect(() => {
    loadData();
  }, []);

  const getIncidentName = (id) => {
    const inc = INCIDENTS.find(i => i.id === id);
    return inc ? `${inc.name} — ${inc.state}` : id;
  };

  const handleTakeUp = (card) => {
    setSelectedCard(card);
  };

  const handleTakeUpSuccess = (updatedCard) => {
    setAllCards(prev => prev.map(c => c.id === updatedCard.id ? { ...c, ...updatedCard, fulfilled: true } : c));
    showToast(`Claimed need: ${updatedCard.item}`, 'success');
  };

  // Filter cards
  const myCommitments = allCards.filter(c => c.done_by === volunteerName);
  const availableNeeds = allCards.filter(c => c.show_pd === true && c.fulfilled === false && c.done_by === null);

  return (
    <div className="relative">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-1">Welcome back, {volunteerName}</h1>
        <p className="text-sm text-text-secondary">View available relief needs, register to assist, and coordinate resource fulfillment.</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">My Commitments</h3>
            <p className="text-3xl font-mono font-bold text-accent-green">
              {loading ? <Skeleton width="w-16" height="h-8" /> : myCommitments.length}
            </p>
          </div>
          <div className="p-3 bg-accent-green/10 text-accent-green rounded-full">
            <CheckCircle2 size={24} />
          </div>
        </div>

        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">Available Needs</h3>
            <p className="text-3xl font-mono font-bold text-accent-blue">
              {loading ? <Skeleton width="w-16" height="h-8" /> : availableNeeds.length}
            </p>
          </div>
          <div className="p-3 bg-accent-blue/10 text-accent-blue rounded-full">
            <ClipboardList size={24} />
          </div>
        </div>

        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center justify-between">
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider mb-2">Active Incidents</h3>
            <p className="text-3xl font-mono font-bold text-text-primary">
              {INCIDENTS.length}
            </p>
          </div>
          <div className="p-3 bg-accent-red/10 text-accent-red rounded-full">
            <Heart size={24} />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-border">
        <button
          onClick={() => setActiveTab('available')}
          className={`px-4 py-3 font-bold text-sm border-b-2 transition-colors ${
            activeTab === 'available'
              ? 'border-accent-blue text-accent-blue'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          Available Needs ({availableNeeds.length})
        </button>
        <button
          onClick={() => setActiveTab('commitments')}
          className={`px-4 py-3 font-bold text-sm border-b-2 transition-colors ${
            activeTab === 'commitments'
              ? 'border-accent-green text-accent-green'
              : 'border-transparent text-text-secondary hover:text-text-primary'
          }`}
        >
          My Commitments ({myCommitments.length})
        </button>
      </div>

      {/* Tab Content */}
      {loading ? (
        <div className="space-y-6">
          <Skeleton height="h-32" />
          <Skeleton height="h-32" />
        </div>
      ) : activeTab === 'available' ? (
        <div>
          {availableNeeds.length === 0 ? (
            <div className="bg-bg-card border border-border rounded-lg p-12 text-center text-text-secondary">
              <h3 className="text-lg font-bold text-text-primary mb-1">No available needs right now</h3>
              <p className="text-sm">All relief cards are currently assigned or completed. Thank you!</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
              <AnimatePresence>
                {availableNeeds.map((card, index) => (
                  <motion.div
                    key={card.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                  >
                    <PublicNeedCard
                      needCard={card}
                      incidentName={getIncidentName(card.incident_id)}
                      onTakeUp={handleTakeUp}
                      onDonate={() => {}}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      ) : (
        <div>
          {myCommitments.length === 0 ? (
            <div className="bg-bg-card border border-border rounded-lg p-12 text-center text-text-secondary">
              <h3 className="text-lg font-bold text-text-primary mb-1">No commitments registered</h3>
              <p className="text-sm">Select tasks from the "Available Needs" tab to begin assisting.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {myCommitments.map((card) => (
                <motion.div
                  key={card.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-bg-card border border-border rounded-lg p-5 flex items-start justify-between shadow-sm"
                >
                  <div className="flex-grow">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 bg-accent-green/10 text-accent-green text-xs font-bold rounded uppercase tracking-wider">
                        {card.type}
                      </span>
                      <h3 className="font-bold text-text-primary font-serif text-lg">{card.quantity} × {card.item}</h3>
                    </div>
                    <p className="text-sm text-text-secondary mb-3">{card.explanation}</p>
                    {card.note && (
                      <div className="px-3 py-1.5 bg-accent-amber/10 border-l-2 border-accent-amber text-accent-amber text-xs font-bold inline-block mb-3">
                        ⚠ Note: {card.note}
                      </div>
                    )}
                    <div className="text-xs text-text-muted">
                      Incident: <span className="font-medium text-text-secondary">{getIncidentName(card.incident_id)}</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <span className="px-3 py-1 bg-accent-green text-white text-xs font-bold rounded-full uppercase tracking-wider">
                      Fulfilling
                    </span>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Take Up Modal */}
      {selectedCard && (
        <TakeUpModal
          needCard={selectedCard}
          incidentName={getIncidentName(selectedCard.incident_id)}
          onClose={() => setSelectedCard(null)}
          onSuccess={handleTakeUpSuccess}
        />
      )}
    </div>
  );
}
