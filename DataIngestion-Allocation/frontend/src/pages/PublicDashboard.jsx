import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { api, getIncident, isDemoModeEnabled, setDemoMode as setDemoModeGlobal, initDemoMode } from '../services/api';
import { updateCardInList } from '../utils/api';
import { INCIDENTS } from '../data/incidents';
import { PublicNeedCard, ActivityFeed, TakeUpModal, Skeleton, LivePulse } from '../components';
import { usePageTitle } from '../hooks/usePageTitle';
import { usePolling } from '../hooks/usePolling';
import { useToast } from '../components/ToastProvider';
import { Search, Settings } from 'lucide-react';

const filterTabs = [
  { label: 'Open', value: 'open' },
  { label: 'All', value: 'all' },
  { label: 'Food', value: 'send_food' },
  { label: 'Medicine', value: 'send_meds' },
  { label: 'Water', value: 'send_water' },
  { label: 'Rescue', value: 'send_rescue_team' },
  { label: 'Resources', value: 'reserve_resource' },
  { label: 'Taken', value: 'taken' },
];

export default function PublicDashboard() {
  usePageTitle('Public Dashboard');
  const navigate = useNavigate();
  const showToast = useToast();
  
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [needCards, setNeedCards] = useState([]);
  const [feedItems, setFeedItems] = useState([]);
  const [fulfilledCount, setFulfilledCount] = useState(0);
  const [error, setError] = useState(null);
  const [demoMode, setDemoModeState] = useState(isDemoModeEnabled());
  const [currentIncident, setCurrentIncident] = useState(getIncident());
  
  const [activeFilter, setActiveFilter] = useState('all');
  const [selectedCard, setSelectedCard] = useState(null);

  // Update currentIncident when component mounts or when navigating back
  useEffect(() => {
    const incident = getIncident();
    console.log('IncidentSetupPage: Got incident from localStorage:', incident);
    setCurrentIncident(incident);
  }, []);

  // Handle demo mode toggle
  const handleDemoModeToggle = () => {
    const newMode = !demoMode;
    setDemoModeGlobal(newMode);
    setDemoModeState(newMode);
    showToast(`Demo mode ${newMode ? 'enabled' : 'disabled'}`, 'info');
    // Refresh data after switching modes
    fetchData();
  };

  // Handle search latest incidents
  const handleSearchLatestIncidents = async () => {
    if (!currentIncident) {
      showToast('No incident selected', 'error');
      return;
    }

    setSearching(true);
    try {
      console.log('Calling api.createIncident with:', currentIncident.name);
      const res = await api.createIncident(currentIncident.name);
      console.log('API response:', res);
      
      if (res.error) {
        showToast(`Search failed: ${res.error}`, 'error');
        setSearching(false);
        return;
      }

      // Refresh need cards after search
      await fetchData();
      showToast('Latest incidents searched and resources allocated', 'success');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Search failed';
      showToast(errorMsg, 'error');
    } finally {
      setSearching(false);
    }
  };

  // Fetch data from API
  const fetchData = async () => {
    try {
      const [allCardsRes, feedRes] = await Promise.all([
        api.getAllNeedCards(),
        api.getActivityFeed()
      ]);

      if (allCardsRes.error) {
        setError(allCardsRes.error);
        showToast(`Error fetching data: ${allCardsRes.error}`, 'error');
        return;
      }

      if (allCardsRes.data) {
        setNeedCards(allCardsRes.data);
        setFulfilledCount(allCardsRes.data.filter(c => c.fulfilled).length);
        setError(null);
      }
      
      if (feedRes.data) {
        setFeedItems(feedRes.data);
      }
      
      setLoading(false);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMsg);
      showToast(errorMsg, 'error');
    }
  };

  // Use polling hook for auto-refresh
  const pollInterval = parseInt(import.meta.env.VITE_POLL_INTERVAL_MS || '30000');
  usePolling(fetchData, pollInterval, true);

  // Simulate new feed item every 12s
  useEffect(() => {
    if (feedItems.length === 0) return;

    const interval = setInterval(() => {
      setFeedItems(prev => {
        // Pick a random past event to "re-occur" or just duplicate the oldest one to the top
        const randomIndex = Math.floor(Math.random() * prev.length);
        const newItem = { 
          ...prev[randomIndex], 
          id: `sim_${Date.now()}`, 
          timestamp: new Date().toISOString() 
        };
        return [newItem, ...prev].slice(0, 50); // keep max 50
      });
    }, 12000);

    return () => clearInterval(interval);
  }, [feedItems.length]);

  const handleTakeUp = (card) => {
    setSelectedCard(card);
  };

  const handleDonate = (card) => {
    navigate(`/contribute/${card.id}`, { state: { mode: 'donate' } });
  };

  const handleTakeUpSuccess = (updatedCard) => {
    setNeedCards(prev => updateCardInList(prev, updatedCard));
  };

  // Derived state - filter for public dashboard
  const publicCards = needCards.filter(card => card.show_pd === true);
  
  let filteredCards;
  if (activeFilter === 'open') {
    filteredCards = publicCards.filter(card => card.fulfilled === false);
  } else if (activeFilter === 'taken') {
    filteredCards = publicCards.filter(card => card.fulfilled === true);
  } else if (activeFilter === 'all') {
    filteredCards = publicCards;
  } else {
    filteredCards = publicCards.filter(card => card.tool_name === activeFilter);
  }
  
  // Group by incident
  const groupedCards = filteredCards.reduce((acc, card) => {
    if (!acc[card.incident_id]) acc[card.incident_id] = [];
    acc[card.incident_id].push(card);
    return acc;
  }, {});

  const getIncidentName = (id) => {
    const inc = INCIDENTS.find(i => i.id === id);
    return inc ? `${inc.name} — ${inc.state}` : id;
  };

  return (
    <div className="bg-bg-primary min-h-screen pb-12">
      {/* Top Stats Bar */}
      <div className="bg-bg-card border-b border-border">
        <div className="max-w-[1400px] mx-auto px-6 py-6 grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-4 divide-y md:divide-y-0 md:divide-x divide-border">
          <div className="flex flex-col items-center text-center px-4">
            <span className="text-3xl font-mono font-bold text-text-primary">
              {loading ? <Skeleton width="w-16" height="h-8" /> : needCards.length}
            </span>
            <span className="text-xs uppercase tracking-wider font-bold text-text-secondary mt-1">Open Needs</span>
          </div>
          <div className="flex flex-col items-center text-center px-4 pt-6 md:pt-0">
            <span className="text-3xl font-mono font-bold text-accent-green">
              {loading ? <Skeleton width="w-16" height="h-8" /> : fulfilledCount}
            </span>
            <span className="text-xs uppercase tracking-wider font-bold text-text-secondary mt-1">Needs Fulfilled Today</span>
          </div>
          <div className="flex flex-col items-center text-center px-4 pt-6 md:pt-0">
            <span className="text-3xl font-mono font-bold text-text-primary">{INCIDENTS.length}</span>
            <span className="text-xs uppercase tracking-wider font-bold text-text-secondary mt-1">Active Incidents</span>
          </div>
          <div className="flex flex-col items-center text-center px-4 pt-6 md:pt-0">
            <span className="text-3xl font-mono font-bold text-text-primary">47</span>
            <span className="text-xs uppercase tracking-wider font-bold text-text-secondary mt-1">Volunteers Active</span>
          </div>
        </div>
      </div>

      {/* Control Bar — Demo Mode & Search */}
      <div className="bg-bg-secondary border-b border-border">
        <div className="max-w-[1400px] mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            {/* Demo Mode Toggle */}
            <div className="flex items-center gap-3">
              <span className="text-xs font-bold text-text-secondary uppercase tracking-wider">Demo Mode:</span>
              <button
                onClick={handleDemoModeToggle}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  demoMode ? 'bg-accent-blue' : 'bg-border'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    demoMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className={`text-xs font-bold ${demoMode ? 'text-accent-blue' : 'text-text-muted'}`}>
                {demoMode ? 'ON' : 'OFF'}
              </span>
            </div>

            {/* Current Incident Display */}
            {currentIncident && (
              <div className="text-xs text-text-secondary">
                Tracking: <span className="font-bold text-text-primary">{currentIncident.name}</span>
              </div>
            )}
          </div>

          {/* Search Latest Incidents Button */}
          <button
            onClick={handleSearchLatestIncidents}
            disabled={searching || !currentIncident}
            className="flex items-center justify-center gap-2 px-4 py-2 bg-accent-blue text-white font-bold text-sm rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Search size={16} />
            {searching ? 'Searching...' : 'Search Latest Incidents'}
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-[1400px] mx-auto px-6 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          
          {/* Left Column — Open Needs Feed */}
          <div className="lg:w-[70%]">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
              <div className="flex items-center gap-3">
                <h2 className="text-2xl font-bold tracking-tight text-text-primary">Open Needs</h2>
                <span className="bg-bg-secondary text-text-secondary px-2.5 py-0.5 rounded-full text-xs font-bold font-mono">
                  {filteredCards.length}
                </span>
              </div>
              
              {/* Filters */}
              <div className="flex flex-wrap gap-2">
                {filterTabs.map(tab => (
                  <button
                    key={tab.value}
                    onClick={() => setActiveFilter(tab.value)}
                    className={`px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-colors ${
                      activeFilter === tab.value 
                        ? 'bg-text-primary text-white' 
                        : 'bg-bg-card border border-border text-text-secondary hover:bg-border'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {loading ? (
              <div className="space-y-6">
                <Skeleton height="h-48" />
                <Skeleton height="h-48" />
                <Skeleton height="h-48" />
              </div>
            ) : filteredCards.length === 0 ? (
              <div className="bg-bg-card border border-border rounded-lg p-12 text-center text-text-secondary">
                {activeFilter === 'open' && "No open needs right now — all needs are currently fulfilled or under review."}
                {activeFilter === 'taken' && "No taken needs yet — volunteers haven't fulfilled any needs."}
                {activeFilter === 'all' && "No needs found."}
                {!['open', 'taken', 'all'].includes(activeFilter) && `No ${activeFilter.replace('send_', '')} needs found.`}
              </div>
            ) : (
              <div className="space-y-8">
                {Object.entries(groupedCards).map(([incidentId, cards]) => (
                  <div key={incidentId}>
                    {/* Section Divider */}
                    <div className="flex items-center gap-4 mb-4">
                      <h3 className="text-sm font-bold text-text-muted uppercase tracking-wider whitespace-nowrap">
                        {getIncidentName(incidentId)}
                      </h3>
                      <div className="h-px bg-border flex-grow"></div>
                    </div>
                    
                    {/* Cards */}
                    <div className="space-y-4">
                      <AnimatePresence mode="popLayout">
                        {cards.map((card, index) => (
                          <motion.div
                            key={card.id}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.08 }}
                            layout
                          >
                            <PublicNeedCard 
                              needCard={card} 
                              incidentName={getIncidentName(incidentId)}
                              onTakeUp={handleTakeUp}
                              onDonate={handleDonate}
                            />
                          </motion.div>
                        ))}
                      </AnimatePresence>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right Column — Live Activity */}
          <div className="lg:w-[30%] flex flex-col">
            <div className="sticky top-6">
              <div className="flex items-center gap-3 mb-4">
                <h2 className="text-2xl font-bold tracking-tight text-text-primary">Live Activity</h2>
              </div>
              
              <ActivityFeed items={feedItems} maxHeight="max-h-[600px]" />
            </div>
          </div>
          
        </div>
      </div>

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
