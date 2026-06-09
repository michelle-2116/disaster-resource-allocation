import React, { useEffect, useMemo, useState, useCallback } from 'react';
import axios from 'axios';
import DisasterMap from '../components/Map';
import { usePageTitle } from '../hooks/usePageTitle';
import { useToast } from '../components/ToastProvider';
import {
  AlertTriangle,
  CheckCircle,
  CircleSlash,
  MessageSquareWarning,
  Package,
  RefreshCcw,
  Route,
  ShieldAlert,
  Truck,
  Warehouse,
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_ROUTE_API_BASE_URL || 'http://localhost:8001';

const quickReports = [
  'Discord: Floodwater blocking Chundale bridge near Vythiri',
  'Discord: Landslide reported near Meppadi road, ambulance cannot pass',
  'Discord: Fallen tree blocks Panamaram approach road',
];

export default function LogisticsMap() {
  usePageTitle('Logistics Map');
  const showToast = useToast();

  const [data, setData] = useState({
    incidents: [],
    shelters: [],
    dispatches: [],
    need_cards: [],
    warehouses: [],
    inventory: [],
    blocked_roads: [],
  });

  const [blockForm, setBlockForm] = useState({
    lat: '11.5797',
    lng: '76.0735',
    radius_meters: '850',
    reason: 'Floodwater over Chundale bridge',
  });

  const [discordMessage, setDiscordMessage] = useState(quickReports[0]);
  const [loading, setLoading] = useState(false);
  const [lastAction, setLastAction] = useState('');
  const [activeControlTab, setActiveControlTab] = useState('roadblocks'); // 'roadblocks' or 'warehouses'

  const loadAll = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/map-data`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch map data:', err);
    }
  }, []);

  useEffect(() => {
    loadAll();
    const interval = setInterval(loadAll, 5000);
    return () => clearInterval(interval);
  }, [loadAll]);

  const pendingNeeds = useMemo(
    () => data.need_cards?.filter((need) => need.status === 'pending_approval') ?? [],
    [data.need_cards],
  );

  const routeStats = useMemo(() => {
    const totalKm = (data.dispatches ?? []).reduce((sum, dispatch) => sum + (dispatch.distance || 0) / 1000, 0);
    const rerouted = [...(data.dispatches ?? []), ...(data.suggested_routes ?? [])].filter((route) => route.rerouted).length;
    return { totalKm, rerouted };
  }, [data.dispatches, data.suggested_routes]);

  const routeExplanations = useMemo(
    () => [...(data.dispatches ?? []), ...(data.suggested_routes ?? [])],
    [data.dispatches, data.suggested_routes],
  );

  const handleMapBlockPoint = useCallback(({ lat, lng }) => {
    setBlockForm((prev) => ({ ...prev, lat, lng }));
    setLastAction(`Selected map coordinates ${lat}, ${lng}. Fill details and submit form.`);
    showToast(`Selected coordinates: ${lat}, ${lng}`, 'info');
  }, [showToast]);

  const handleApprove = useCallback(async (id) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/allocate/approve/${id}`);
      showToast('Allocation route approved and dispatched!', 'success');
      await loadAll();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to approve allocation route', 'error');
    } finally {
      setLoading(false);
    }
  }, [loadAll, showToast]);

  const handleAdminBlock = useCallback(async (event) => {
    event.preventDefault();
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/blocked-roads`, {
        lat: Number(blockForm.lat),
        lng: Number(blockForm.lng),
        radius_meters: Number(blockForm.radius_meters),
        reason: blockForm.reason,
        source: 'admin',
      });
      showToast('Road block successfully added and routes recalculated!', 'success');
      await loadAll();
      setLastAction('Road block added. Suggested and active routes were recalculated around the blocked radius.');
    } catch (err) {
      showToast('Failed to add roadblock', 'error');
    } finally {
      setLoading(false);
    }
  }, [blockForm, loadAll, showToast]);

  const handleDiscordBlock = useCallback(async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/discord/road-report`, {
        message: discordMessage,
        author: 'wayanad-relief-discord',
      });
      showToast('Discord report processed and road blocked!', 'success');
      await loadAll();
      setLastAction('Discord road report ingested. Routes were recalculated with the new road block.');
    } catch (err) {
      showToast('Failed to parse Discord message location', 'error');
    } finally {
      setLoading(false);
    }
  }, [discordMessage, loadAll, showToast]);

  const handleReset = useCallback(async () => {
    if (window.confirm('Are you sure you want to reset the simulation state? This wipes roadblocks, dispatches, and resets inventory counts.')) {
      try {
        await axios.post(`${API_BASE}/system/reset`);
        showToast('Simulation state reset successfully', 'info');
        await loadAll();
      } catch (err) {
        showToast('Failed to reset simulation state', 'error');
      }
    }
  }, [loadAll, showToast]);

  return (
    <div className="relative space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-text-primary mb-1 flex items-center gap-3">
            <Route className="text-accent-blue" size={30} /> Aegis Logistics Map
          </h1>
          <p className="text-sm text-text-secondary">Track live disaster incidents, roadblock detours, and active dispatch paths.</p>
        </div>
        <button
          onClick={handleReset}
          className="flex items-center gap-2 px-4 py-2 bg-bg-card border border-border rounded hover:bg-bg-secondary hover:text-accent-red transition-colors text-text-primary font-medium text-sm"
          title="Reset simulation state"
        >
          <RefreshCcw size={16} />
          Reset Simulation
        </button>
      </div>

      {/* Stats Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center gap-4">
          <AlertTriangle size={32} className="text-accent-red shrink-0" />
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Active Incidents</h3>
            <p className="text-2xl font-mono font-bold text-text-primary mt-1">{data.incidents?.length ?? 0}</p>
          </div>
        </div>
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center gap-4">
          <ShieldAlert size={32} className="text-accent-amber shrink-0" />
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Roadblocks</h3>
            <p className="text-2xl font-mono font-bold text-text-primary mt-1">{data.blocked_roads?.length ?? 0}</p>
          </div>
        </div>
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center gap-4">
          <Truck size={32} className="text-accent-green shrink-0" />
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Active Dispatches</h3>
            <p className="text-2xl font-mono font-bold text-text-primary mt-1">{data.dispatches?.length ?? 0}</p>
          </div>
        </div>
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center gap-4">
          <Route size={32} className="text-purple-600 shrink-0" />
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Rerouted Paths</h3>
            <p className="text-2xl font-mono font-bold text-text-primary mt-1">{routeStats.rerouted}</p>
          </div>
        </div>
        <div className="bg-bg-card border border-border rounded p-6 shadow-sm flex items-center gap-4">
          <Package size={32} className="text-accent-blue shrink-0" />
          <div>
            <h3 className="text-xs font-bold text-text-secondary uppercase tracking-wider">Planned Distance</h3>
            <p className="text-2xl font-mono font-bold text-text-primary mt-1">{routeStats.totalKm.toFixed(1)} km</p>
          </div>
        </div>
      </div>

      {/* Main Core Layout Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Columns - Interactive Map Container */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="h-[600px] bg-bg-card border border-border rounded-lg overflow-hidden relative shadow-sm">
            <DisasterMap data={data} blockDraft={blockForm} onBlockPointSelected={handleMapBlockPoint} />
          </div>

          {/* Suggested Route Approvals & Live Decisions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Pending Route Approvals */}
            <div className="bg-bg-card border border-border rounded-lg p-5 flex flex-col h-[380px]">
              <h2 className="flex items-center gap-2 font-bold text-sm tracking-wider mb-4 text-accent-blue uppercase shrink-0">
                <Package size={18} /> Pending Route Approvals
              </h2>
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
                {pendingNeeds.map((need) => {
                  const shelter = data.shelters.find((item) => item.id === need.shelter_id);
                  return (
                    <div key={need.id} className="bg-bg-secondary/40 border border-border p-3.5 rounded-lg flex justify-between items-center gap-3">
                      <div className="min-w-0">
                        <p className="text-base font-bold text-text-primary truncate">{need.item_type} x {need.requested_qty}</p>
                        <p className="text-xs text-text-secondary truncate mt-0.5">{shelter?.name || 'Loading shelter...'}</p>
                      </div>
                      <button
                        onClick={() => handleApprove(need.id)}
                        disabled={loading}
                        className="h-10 w-10 shrink-0 inline-flex items-center justify-center rounded-lg bg-accent-blue hover:bg-accent-green text-white transition-colors disabled:opacity-60"
                        title="Approve allocation & compute route path"
                      >
                        <CheckCircle size={18} />
                      </button>
                    </div>
                  );
                })}
                {pendingNeeds.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-text-muted py-8">
                    <span className="text-lg">✓</span>
                    <p className="text-sm mt-1">No pending routing allocations.</p>
                  </div>
                )}
              </div>
            </div>

            {/* Active Route Decisions & Explanations */}
            <div className="bg-bg-card border border-border rounded-lg p-5 flex flex-col h-[380px]">
              <h2 className="flex items-center gap-2 font-bold text-sm tracking-wider mb-4 text-accent-green uppercase shrink-0">
                <Truck size={18} /> Route Explanations
              </h2>
              <div className="flex-1 overflow-y-auto space-y-3 pr-1 custom-scrollbar">
                {routeExplanations.map((route) => (
                  <div key={route.id} className="bg-bg-secondary/40 p-3.5 rounded-lg border border-border">
                    <div className="flex justify-between gap-3 text-xs mb-1.5 font-semibold">
                      <span className={route.status === 'suggested' ? 'text-accent-amber truncate' : 'text-accent-green truncate'}>
                        {route.status === 'suggested' ? 'Suggested path' : 'Active dispatch'}
                      </span>
                      <span className="text-text-secondary font-mono">{(route.distance / 1000).toFixed(1)} km</span>
                    </div>
                    <p className="text-sm font-bold text-text-primary truncate">{route.item_type} to {route.shelter_name}</p>
                    <p className="mt-1.5 text-xs text-text-secondary leading-relaxed">{route.route_explanation}</p>
                    <div className="mt-2.5 flex items-center justify-between gap-3 text-[11px] text-text-muted">
                      <span>{Math.round(route.estimated_time / 60)} min ETA</span>
                      <span className={route.rerouted ? 'text-purple-600 font-medium' : 'text-text-muted'}>
                        {route.rerouted ? `avoids roadblock` : 'direct optimized'}
                      </span>
                    </div>
                  </div>
                ))}
                {routeExplanations.length === 0 && (
                  <div className="flex flex-col items-center justify-center h-full text-center text-text-muted py-8">
                    <p className="text-sm">Approve a need route to view path explanations.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Side Panels & Controls */}
        <div className="flex flex-col gap-6">
          
          {/* Tabs header */}
          <div className="flex border-b border-border">
            <button
              onClick={() => setActiveControlTab('roadblocks')}
              className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-colors ${
                activeControlTab === 'roadblocks'
                  ? 'border-accent-blue text-accent-blue'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              Roadblocks & Alerts
            </button>
            <button
              onClick={() => setActiveControlTab('warehouses')}
              className={`flex-1 pb-3 text-sm font-bold border-b-2 transition-colors ${
                activeControlTab === 'warehouses'
                  ? 'border-accent-blue text-accent-blue'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              Warehouses
            </button>
          </div>

          {/* Roadblocks Form & Ingestion Panel */}
          {activeControlTab === 'roadblocks' && (
            <div className="space-y-6">
              
              {/* Add roadblock Form */}
              <div className="bg-bg-card border border-border rounded-lg p-5">
                <h2 className="flex items-center gap-2 font-bold text-sm tracking-wider mb-4 text-text-primary uppercase">
                  <CircleSlash size={16} /> Plot Road Block
                </h2>
                <form onSubmit={handleAdminBlock} className="space-y-4">
                  <p className="text-xs text-text-secondary leading-relaxed">
                    Click coordinates directly on the map to autofill latitude and longitude.
                  </p>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="text-[10px] font-bold uppercase text-text-secondary block mb-1">Latitude</label>
                      <input
                        className="w-full bg-bg-secondary border border-border rounded px-2.5 py-1.5 text-xs font-mono outline-none focus:border-accent-blue text-text-primary"
                        value={blockForm.lat}
                        onChange={(event) => setBlockForm({ ...blockForm, lat: event.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-text-secondary block mb-1">Longitude</label>
                      <input
                        className="w-full bg-bg-secondary border border-border rounded px-2.5 py-1.5 text-xs font-mono outline-none focus:border-accent-blue text-text-primary"
                        value={blockForm.lng}
                        onChange={(event) => setBlockForm({ ...blockForm, lng: event.target.value })}
                        required
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-bold uppercase text-text-secondary block mb-1">Radius (m)</label>
                      <input
                        className="w-full bg-bg-secondary border border-border rounded px-2.5 py-1.5 text-xs font-mono outline-none focus:border-accent-blue text-text-primary"
                        value={blockForm.radius_meters}
                        onChange={(event) => setBlockForm({ ...blockForm, radius_meters: event.target.value })}
                        required
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-[10px] font-bold uppercase text-text-secondary block mb-1">Reason / Description</label>
                    <input
                      className="w-full bg-bg-secondary border border-border rounded px-2.5 py-1.5 text-xs outline-none focus:border-accent-blue text-text-primary"
                      value={blockForm.reason}
                      onChange={(event) => setBlockForm({ ...blockForm, reason: event.target.value })}
                      required
                    />
                  </div>
                  <button
                    disabled={loading}
                    className="w-full bg-accent-blue hover:bg-accent-blue-light hover:text-accent-blue bg-accent-blue text-white py-2 rounded text-xs font-bold transition-colors disabled:opacity-60 shadow-sm"
                  >
                    Add Road Block
                  </button>
                  {lastAction && <p className="text-[11px] text-accent-blue mt-2 leading-relaxed bg-accent-blue/5 p-2 border border-accent-blue/10 rounded">{lastAction}</p>}
                </form>
              </div>

              {/* Ingest Roadblock from Discord */}
              <div className="bg-bg-card border border-border rounded-lg p-5">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="flex items-center gap-2 font-bold text-sm tracking-wider text-text-primary uppercase">
                    <MessageSquareWarning size={16} /> Discord Ingestion
                  </h2>
                  <select
                    className="max-w-[150px] bg-bg-secondary border border-border rounded px-2.5 py-1 text-xs text-text-secondary outline-none"
                    value={discordMessage}
                    onChange={(event) => setDiscordMessage(event.target.value)}
                  >
                    {quickReports.map((report) => (
                      <option key={report} value={report}>{report.replace('Discord: ', '')}</option>
                    ))}
                  </select>
                </div>
                <textarea
                  className="w-full h-20 bg-bg-secondary border border-border rounded px-2.5 py-2 text-xs outline-none focus:border-accent-blue text-text-primary resize-none mb-3 font-mono leading-relaxed"
                  value={discordMessage}
                  onChange={(event) => setDiscordMessage(event.target.value)}
                />
                <button
                  disabled={loading}
                  onClick={handleDiscordBlock}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded text-xs font-bold transition-colors disabled:opacity-60 shadow-sm"
                >
                  Ingest Discord road block
                </button>
              </div>

              {/* Active roadblock list */}
              <div className="bg-bg-card border border-border rounded-lg p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="font-bold text-xs uppercase text-text-secondary tracking-wider">Marked roadblocks</h2>
                  <span className="text-xs font-mono font-bold text-accent-amber bg-accent-amber/10 px-2 py-0.5 rounded-full">{data.blocked_roads?.length ?? 0}</span>
                </div>
                <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1 custom-scrollbar">
                  {data.blocked_roads?.map((block) => (
                    <div key={block.id} className="bg-bg-secondary/40 border border-border/80 p-2.5 rounded-lg">
                      <p className="text-xs font-bold text-text-primary">{block.reason}</p>
                      <p className="text-[10px] text-text-muted mt-1 font-mono">
                        {Number(block.lat).toFixed(4)}, {Number(block.lng).toFixed(4)} | {Math.round(block.radius_meters ?? 800)}m | {block.source}
                      </p>
                    </div>
                  ))}
                  {(!data.blocked_roads || data.blocked_roads.length === 0) && (
                    <p className="text-xs text-text-muted text-center py-4">No active roadblocks.</p>
                  )}
                </div>
              </div>

            </div>
          )}

          {/* Warehouses inventory panel */}
          {activeControlTab === 'warehouses' && (
            <div className="bg-bg-card border border-border rounded-lg p-5 flex flex-col max-h-[650px]">
              <div className="flex items-center justify-between mb-4 shrink-0">
                <h2 className="flex items-center gap-2 font-bold text-sm tracking-wider text-text-primary uppercase">
                  <Warehouse size={16} /> Warehouse Stocks
                </h2>
                <span className="text-xs text-accent-blue bg-accent-blue/10 px-2 py-0.5 rounded-full font-bold">{data.warehouses?.length ?? 0} Hubs</span>
              </div>
              <div className="flex-1 overflow-y-auto space-y-4 pr-1 custom-scrollbar">
                {data.warehouses?.map((warehouse) => (
                  <div key={warehouse.id} className="border border-border bg-bg-secondary/40 p-3 rounded-lg">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-sm font-bold text-text-primary">{warehouse.name}</p>
                        <p className="text-[10px] text-text-muted mt-0.5">Route Access: {warehouse.access}</p>
                      </div>
                      <span className="text-[9px] bg-accent-blue/10 text-accent-blue px-2 py-0.5 rounded-full uppercase font-bold tracking-wider">{warehouse.type.replace('_', ' ')}</span>
                    </div>
                    <div className="mt-2.5 grid grid-cols-2 gap-2">
                      {warehouse.resources.map((item) => (
                        <div key={item.item_name} className="bg-bg-card border border-border p-2 rounded">
                          <div className="flex items-center justify-between gap-1.5">
                            <span className="text-[11px] text-text-secondary truncate">{item.item_name}</span>
                            <span className="text-xs font-mono font-bold text-text-primary">{item.quantity}</span>
                          </div>
                          <p className="text-[9px] text-text-muted mt-0.5">{item.unit} | {item.priority}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>

      </div>
    </div>
  );
}
