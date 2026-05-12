import { NEED_CARDS } from '../data/needCards';
import { INCIDENTS } from '../data/incidents';
import { ACTIVITY_FEED } from '../data/activityFeed';

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Global state - SINGLE SOURCE OF TRUTH
let demoModeEnabled = false;
let currentNeedCards = [...NEED_CARDS];
let currentIncidents = [...INCIDENTS];
let currentActivityFeed = [...ACTIVITY_FEED];

// Incident persistence
const INCIDENT_STORAGE_KEY = 'current_incident';
const DEMO_MODE_STORAGE_KEY = 'demo_mode_enabled';

// Persistence helpers
export const saveIncident = (incidentName) => {
  localStorage.setItem(INCIDENT_STORAGE_KEY, JSON.stringify({
    name: incidentName,
    savedAt: new Date().toISOString()
  }));
};

export const getIncident = () => {
  const stored = localStorage.getItem(INCIDENT_STORAGE_KEY);
  return stored ? JSON.parse(stored) : null;
};

export const clearIncident = () => {
  localStorage.removeItem(INCIDENT_STORAGE_KEY);
};

export const resetDemoDatabase = async () => {
  try {
    const res = await fetch(`${API_BASE_URL}/demo/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
    const result = await res.json();
    console.log('Demo database reset:', result);
    return { success: true, error: null };
  } catch (error) {
    console.error('Failed to reset demo database:', error);
    return { success: false, error: error.message };
  }
};

export const isDemoModeEnabled = () => {
  const stored = localStorage.getItem(DEMO_MODE_STORAGE_KEY);
  return stored !== null ? JSON.parse(stored) : false;
};

export const setDemoMode = (enabled) => {
  demoModeEnabled = enabled;
  localStorage.setItem(DEMO_MODE_STORAGE_KEY, JSON.stringify(enabled));
  
  // Update data based on mode
  if (enabled) {
    currentNeedCards = [...DEMO_SEED_DATA];
  } else {
    currentNeedCards = [...NEED_CARDS];
  }
};

// Load demo mode from localStorage on startup
export const initDemoMode = () => {
  const stored = localStorage.getItem(DEMO_MODE_STORAGE_KEY);
  if (stored !== null) {
    demoModeEnabled = JSON.parse(stored);
    // Update data based on loaded mode
    if (demoModeEnabled) {
      currentNeedCards = [...DEMO_SEED_DATA];
    } else {
      currentNeedCards = [...NEED_CARDS];
    }
  }
};

// Seed data for demo mode
const DEMO_SEED_DATA = [
  {
    id: "demo_card_001",
    incident_id: "demo_kerala_floods_2026",
    type: "food",
    item: "Rice Packets",
    qty: 500,
    quantity: 500,
    tool_name: "send_food",
    explanation: "Immediate food supply needed for evacuated families in relief camps",
    note: "Distribute through local relief centers",
    fulfilled: false,
    done_by: null,
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_002",
    incident_id: "demo_kerala_floods_2026",
    type: "water",
    item: "Water Purification Tablets",
    qty: 1000,
    quantity: 1000,
    tool_name: "send_water",
    explanation: "Contaminated water sources require purification for drinking",
    note: "Distribute to affected villages",
    fulfilled: false,
    done_by: null,
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_003",
    incident_id: "demo_kerala_floods_2026",
    type: "meds",
    item: "First Aid Kits",
    qty: 50,
    quantity: 50,
    tool_name: "send_meds",
    explanation: "Medical supplies for treating injuries from flooding",
    note: "Send to primary health centers",
    fulfilled: false,
    done_by: null,
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_004",
    incident_id: "demo_earthquake_himachal_2026",
    type: "rescue_team",
    item: "Search and Rescue Team",
    qty: 2,
    quantity: 2,
    tool_name: "send_rescue_team",
    explanation: "Urgent need for rescue teams to search for survivors in collapsed buildings",
    note: "Deploy to Shimla district",
    fulfilled: false,
    done_by: null,
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_005",
    incident_id: "demo_cyclone_odisha_2026",
    type: "food",
    item: "Emergency Rations",
    qty: 1000,
    quantity: 1000,
    tool_name: "send_food",
    explanation: "Pre-positioned supplies for post-cyclone relief",
    note: "Store in safe locations away from storm surge",
    fulfilled: false,
    done_by: null,
    pending_approval: false,
    show_pd: true
  },
  // Pending approval cards (for admin dashboard)
  {
    id: "demo_card_006",
    incident_id: "demo_kerala_floods_2026",
    type: "water",
    item: "Water Tankers",
    qty: 10,
    quantity: 10,
    tool_name: "send_water",
    explanation: "Mobile water distribution units for remote areas",
    note: "High quantity - requires approval",
    fulfilled: false,
    done_by: null,
    pending_approval: true,
    show_pd: false
  },
  {
    id: "demo_card_007",
    incident_id: "demo_earthquake_himachal_2026",
    type: "meds",
    item: "Medical Teams",
    qty: 3,
    quantity: 3,
    tool_name: "send_meds",
    explanation: "Specialized medical teams for trauma care",
    note: "Pending admin review",
    fulfilled: false,
    done_by: null,
    pending_approval: true,
    show_pd: false
  },
  // Fulfilled/taken cards
  {
    id: "demo_card_008",
    incident_id: "demo_kerala_floods_2026",
    type: "food",
    item: "Cooked Meals",
    qty: 200,
    quantity: 200,
    tool_name: "send_food",
    explanation: "Hot meals for relief workers and evacuees",
    note: "Distributed by NGO",
    fulfilled: true,
    done_by: "Kerala Relief Foundation",
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_009",
    incident_id: "demo_cyclone_odisha_2026",
    type: "water",
    item: "Drinking Water Bottles",
    qty: 500,
    quantity: 500,
    tool_name: "send_water",
    explanation: "Safe drinking water for affected population",
    note: "Delivered to camps",
    fulfilled: true,
    done_by: "Odisha Water Relief",
    pending_approval: false,
    show_pd: true
  },
  {
    id: "demo_card_010",
    incident_id: "demo_earthquake_himachal_2026",
    type: "rescue_team",
    item: "NDRF Team",
    qty: 1,
    quantity: 1,
    tool_name: "send_rescue_team",
    explanation: "National Disaster Response Force deployment",
    note: "Active rescue operations",
    fulfilled: true,
    done_by: "NDRF Unit 5",
    pending_approval: false,
    show_pd: true
  }
];


// Helper to simulate network delay
const delay = (min = 400, max = 800) => {
  const ms = Math.floor(Math.random() * (max - min + 1)) + min;
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Normalize card: convert qty to quantity for FE consistency
const normalizeCard = (card) => ({
  ...card,
  quantity: card.qty || card.quantity,
  tool_name: card.type === 'food' ? 'send_food' : card.type === 'meds' ? 'send_meds' : card.type === 'water' ? 'send_water' : card.type === 'rescue_team' ? 'send_rescue_team' : 'reserve_resource'
});

// ── MOCK API

const mockApi = {
  async getPublicNeedCards() {
    await delay();
    const data = currentNeedCards.filter(
      card => card.show_pd === true && card.fulfilled === false
    );
    return { data, error: null };
  },

  async getPendingApprovalCards() {
    await delay();
    const data = currentNeedCards.filter(
      card => card.pending_approval === true && card.show_pd === false && card.fulfilled === false
    );
    return { data, error: null };
  },

  async getAllNeedCards() {
    await delay();
    return { data: currentNeedCards, error: null };
  },

  async submitDecision(needCardId, approved) {
    await delay();
    const index = currentNeedCards.findIndex(card => card.id === needCardId);
    if (index === -1) {
      return { data: null, error: "Need card not found" };
    }

    const updatedCard = { ...currentNeedCards[index] };
    if (approved) {
      updatedCard.show_pd = true;
      updatedCard.pending_approval = false;
    } else {
      updatedCard.pending_approval = false;
      updatedCard.show_pd = false;
    }

    currentNeedCards[index] = updatedCard;
    currentActivityFeed.unshift({
      id: `log_${Date.now()}`,
      type: "admin",
      message: `Admin ${approved ? 'approved' : 'rejected'} need card: ${updatedCard.item}`,
      timestamp: new Date().toISOString()
    });

    return { data: updatedCard, error: null };
  },

  async takeUpNeedCard(id, name, phone, email) {
    await delay();
    const index = currentNeedCards.findIndex(card => card.id === id);
    if (index === -1) {
      return { data: null, error: "Need card not found" };
    }

    const updatedCard = { ...currentNeedCards[index] };
    updatedCard.done_by = name;
    currentNeedCards[index] = updatedCard;

    currentActivityFeed.unshift({
      id: `log_${Date.now()}`,
      type: "volunteer",
      message: `${name} took up: ${updatedCard.item}`,
      timestamp: new Date().toISOString()
    });

    return { 
      data: { success: true, need_card_id: id, assigned_to: name }, 
      error: null 
    };
  },

  async createIncident(incidentName) {
    await delay(8500, 8500);
    const newIncident = {
      incident_id: `inc_${Date.now()}`,
      name: incidentName,
      status: "verifying"
    };

    currentActivityFeed.unshift({
      id: `log_${Date.now()}`,
      type: "system",
      message: `New incident registered: ${incidentName} (${newIncident.incident_id})`,
      timestamp: new Date().toISOString()
    });

    return { data: newIncident, error: null };
  },

  async getActivityFeed() {
    await delay();
    const data = [...currentActivityFeed].sort(
      (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    return { data, error: null };
  }
};

// ── REAL API ──────────────────────────────────────────────────────────────

const realApi = {
  async getPublicNeedCards() {
    try {
      const res = await fetch(`${API_BASE_URL}/need-cards`);
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const data = await res.json();
      return { data: data.map(normalizeCard), error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async getPendingApprovalCards() {
    try {
      const res = await fetch(`${API_BASE_URL}/need-cards`);
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const allCards = await res.json();
      const data = allCards.filter(
        card => card.pending_approval === true && card.show_pd === false && card.fulfilled === false
      );
      return { data: data.map(normalizeCard), error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async getAllNeedCards() {
    try {
      const res = await fetch(`${API_BASE_URL}/need-cards`);
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const data = await res.json();
      return { data: data.map(normalizeCard), error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async submitDecision(needCardId, approved) {
    try {
      const res = await fetch(`${API_BASE_URL}/need-cards/decision`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ need_card_id: needCardId, approved })
      });
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const result = await res.json();
      return { data: normalizeCard(result.card), error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async takeUpNeedCard(id, name, phone, email) {
    try {
      const res = await fetch(`${API_BASE_URL}/need-cards/take-up`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, name, ph_num: phone, email })
      });
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const result = await res.json();
      return { data: normalizeCard(result.card), error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async createIncident(incidentName) {
    try {
      const demoMode = getDemoMode();
      const res = await fetch(`${API_BASE_URL}/incident/new`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          'incident_name': incidentName,
          'demo_mode': demoMode
        })
      });
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const result = await res.json();
      return { data: result.verified_incident, error: null };
    } catch (error) {
      return { data: null, error: error.message };
    }
  },

  async getActivityFeed() {
    try {
      const res = await fetch(`${API_BASE_URL}/activity-feed`);
      if (!res.ok) throw new Error(`${res.status}: ${res.statusText}`);
      const data = await res.json();
      return { data, error: null };
    } catch (error) {
      return { data: [], error: error.message };
    }
  }
};

// ── EXPORT ────────────────────────────────────────────────────────────────

const getDemoMode = () => {
  const stored = localStorage.getItem(DEMO_MODE_STORAGE_KEY);
  return stored !== null ? JSON.parse(stored) : false;
};

export const api = {
  async getPublicNeedCards() {
    return realApi.getPublicNeedCards();
  },

  async getPendingApprovalCards() {
    return realApi.getPendingApprovalCards();
  },

  async getAllNeedCards() {
    return realApi.getAllNeedCards();
  },

  async submitDecision(needCardId, approved) {
    return realApi.submitDecision(needCardId, approved);
  },

  async takeUpNeedCard(id, name, phone, email) {
    return realApi.takeUpNeedCard(id, name, phone, email);
  },

  async createIncident(incidentName) {
    return realApi.createIncident(incidentName);
  },

  async getActivityFeed() {
    return realApi.getActivityFeed();
  }
};
