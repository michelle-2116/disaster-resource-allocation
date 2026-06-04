import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import DisasterMap from './components/Map';
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

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

const quickReports = [
  'Discord: Floodwater blocking Chundale bridge near Vythiri',
  'Discord: Landslide reported near Meppadi road, ambulance cannot pass',
  'Discord: Fallen tree blocks Panamaram approach road',
];

function App() {
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

  const loadAll = async () => {
    const res = await axios.get(`${API_BASE}/map-data`);
    setData(res.data);
  };

  useEffect(() => {
    loadAll();
  }, []);

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

  const handleMapBlockPoint = ({ lat, lng }) => {
    setBlockForm((prev) => ({ ...prev, lat, lng }));
    setLastAction(`Selected road block point ${lat}, ${lng}. Submit the form to recalculate routes.`);
  };

  const handleApprove = async (id) => {
    setLoading(true);
    await axios.post(`${API_BASE}/allocate/approve/${id}`);
    await loadAll();
    setLoading(false);
  };

  const handleAdminBlock = async (event) => {
    event.preventDefault();
    setLoading(true);
    await axios.post(`${API_BASE}/blocked-roads`, {
      lat: Number(blockForm.lat),
      lng: Number(blockForm.lng),
      radius_meters: Number(blockForm.radius_meters),
      reason: blockForm.reason,
      source: 'admin',
    });
    await loadAll();
    setLastAction('Road block added. Suggested and active routes were recalculated around the blocked radius.');
    setLoading(false);
  };

  const handleDiscordBlock = async () => {
    setLoading(true);
    await axios.post(`${API_BASE}/discord/road-report`, {
      message: discordMessage,
      author: 'wayanad-relief-discord',
    });
    await loadAll();
    setLastAction('Discord road report ingested. Routes were recalculated with the new road block.');
    setLoading(false);
  };

  const handleReset = async () => {
    await axios.post(`${API_BASE}/system/reset`);
    await loadAll();
  };

  return (
    <div className="flex h-screen min-w-[1180px] bg-zinc-950 text-zinc-100 overflow-auto font-sans text-base">
      <aside className="w-[520px] shrink-0 bg-zinc-925 border-r border-zinc-800 flex flex-col shadow-2xl z-10">
        <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
          <div>
            <p className="text-sm font-bold uppercase tracking-[0.22em] text-cyan-400">Wayanad Flood Response</p>
            <h1 className="mt-2 text-3xl font-black tracking-tight flex items-center gap-3">
              <Route className="text-cyan-400" size={34} /> Aegis Routing
            </h1>
          </div>
          <button
            onClick={handleReset}
            className="h-12 w-12 inline-flex items-center justify-center rounded-md border border-red-500/30 text-red-300 hover:bg-red-500/10"
            title="Reset simulation"
          >
            <RefreshCcw size={24} />
          </button>
        </div>

        <div className="p-6 space-y-6 flex-1 overflow-y-auto custom-scrollbar">
          <section className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold uppercase text-zinc-400 tracking-widest flex items-center gap-2">
                <Warehouse size={20} /> Warehouses
              </h2>
              <span className="text-sm text-cyan-300">{data.warehouses?.length ?? 0} active</span>
            </div>
            <div className="space-y-3">
              {data.warehouses?.map((warehouse) => (
                <div key={warehouse.id} className="border border-zinc-800 bg-zinc-900 p-4 rounded-md">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-lg font-bold text-white">{warehouse.name}</p>
                      <p className="text-sm text-zinc-500">{warehouse.access}</p>
                    </div>
                    <span className="text-xs uppercase text-emerald-300">{warehouse.type.replace('_', ' ')}</span>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2">
                    {warehouse.resources.map((item) => (
                      <div key={item.item_name} className="bg-zinc-950 border border-zinc-800 p-3 rounded">
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-sm text-zinc-300 truncate">{item.item_name}</span>
                          <span className="text-sm font-mono text-cyan-300">{item.quantity}</span>
                        </div>
                        <p className="text-xs text-zinc-600">{item.unit} | {item.priority}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <h2 className="text-sm font-bold uppercase text-zinc-400 tracking-widest flex items-center gap-2">
              <CircleSlash size={20} /> Road Blocks
            </h2>
            <form onSubmit={handleAdminBlock} className="border border-zinc-800 bg-zinc-900 p-4 rounded-md space-y-4">
              <p className="text-sm text-zinc-400">
                Click anywhere on the map to fill latitude and longitude, then submit to mark the blocked road and recalculate routes.
              </p>
              <div className="grid grid-cols-3 gap-3">
                <input
                  className="bg-zinc-950 border border-zinc-800 rounded px-3 py-3 text-base outline-none focus:border-cyan-500"
                  value={blockForm.lat}
                  onChange={(event) => setBlockForm({ ...blockForm, lat: event.target.value })}
                  aria-label="Latitude"
                />
                <input
                  className="bg-zinc-950 border border-zinc-800 rounded px-3 py-3 text-base outline-none focus:border-cyan-500"
                  value={blockForm.lng}
                  onChange={(event) => setBlockForm({ ...blockForm, lng: event.target.value })}
                  aria-label="Longitude"
                />
                <input
                  className="bg-zinc-950 border border-zinc-800 rounded px-3 py-3 text-base outline-none focus:border-cyan-500"
                  value={blockForm.radius_meters}
                  onChange={(event) => setBlockForm({ ...blockForm, radius_meters: event.target.value })}
                  aria-label="Radius in meters"
                />
              </div>
              <input
                className="w-full bg-zinc-950 border border-zinc-800 rounded px-3 py-3 text-base outline-none focus:border-cyan-500"
                value={blockForm.reason}
                onChange={(event) => setBlockForm({ ...blockForm, reason: event.target.value })}
                aria-label="Block reason"
              />
              <button disabled={loading} className="w-full bg-cyan-600 hover:bg-cyan-500 disabled:opacity-60 py-3 rounded text-base font-bold">
                Add Admin Block
              </button>
              {lastAction && <p className="text-sm text-cyan-300 leading-6">{lastAction}</p>}
            </form>

            <div className="border border-zinc-800 bg-zinc-900 p-4 rounded-md space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-base font-bold text-white">Marked road blocks</p>
                <span className="text-xs font-mono text-orange-300">{data.blocked_roads?.length ?? 0}</span>
              </div>
              <div className="space-y-2 max-h-44 overflow-y-auto custom-scrollbar pr-1">
                {data.blocked_roads?.map((block) => (
                  <div key={block.id} className="bg-zinc-950 border border-orange-500/20 p-3 rounded">
                    <p className="text-sm font-bold text-orange-200">{block.reason}</p>
                    <p className="text-xs text-zinc-500 mt-1">
                      {Number(block.lat).toFixed(4)}, {Number(block.lng).toFixed(4)} | {Math.round(block.radius_meters ?? 800)} m | {block.source}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="border border-zinc-800 bg-zinc-900 p-4 rounded-md space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-base font-bold text-white flex items-center gap-2">
                  <MessageSquareWarning size={20} className="text-violet-300" /> Discord Reports
                </p>
                <select
                  className="max-w-[220px] bg-zinc-950 border border-zinc-800 rounded px-3 py-2 text-sm text-zinc-300"
                  value={discordMessage}
                  onChange={(event) => setDiscordMessage(event.target.value)}
                >
                  {quickReports.map((report) => (
                    <option key={report} value={report}>{report.replace('Discord: ', '')}</option>
                  ))}
                </select>
              </div>
              <textarea
                className="w-full h-28 bg-zinc-950 border border-zinc-800 rounded px-3 py-3 text-base outline-none focus:border-violet-400 resize-none"
                value={discordMessage}
                onChange={(event) => setDiscordMessage(event.target.value)}
              />
              <button disabled={loading} onClick={handleDiscordBlock} className="w-full bg-violet-600 hover:bg-violet-500 disabled:opacity-60 py-3 rounded text-base font-bold">
                Ingest Discord Road Report
              </button>
            </div>
          </section>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-[660px]">
        <div className="min-h-24 border-b border-zinc-800 bg-zinc-950/95 px-6 py-4 flex items-center justify-between gap-6">
          <div className="flex items-center gap-7 flex-wrap">
            <Metric icon={AlertTriangle} label="Active incidents" value={data.incidents?.length ?? 0} tone="text-red-300" />
            <Metric icon={ShieldAlert} label="Blocked roads" value={data.blocked_roads?.length ?? 0} tone="text-orange-300" />
            <Metric icon={Truck} label="Dispatches" value={data.dispatches?.length ?? 0} tone="text-emerald-300" />
            <Metric icon={Route} label="Rerouted" value={routeStats.rerouted} tone="text-violet-300" />
          </div>
          <div className="text-right">
            <p className="text-sm uppercase tracking-widest text-zinc-500">Planned distance</p>
            <p className="text-2xl font-mono text-cyan-300">{routeStats.totalKm.toFixed(1)} km</p>
          </div>
        </div>

        <div className="flex-1 relative min-h-0">
          <DisasterMap data={data} blockDraft={blockForm} onBlockPointSelected={handleMapBlockPoint} />
        </div>

        <div className="h-[360px] min-h-[300px] bg-zinc-925 border-t border-zinc-800 p-6 grid grid-cols-2 gap-6 overflow-hidden">
          <section className="min-w-0 overflow-y-auto custom-scrollbar pr-3">
            <h2 className="flex items-center gap-2 font-black text-sm tracking-widest mb-4 text-cyan-300 uppercase">
              <Package size={22} /> Pending Allocations
            </h2>
            <div className="space-y-3">
              {pendingNeeds.map((need) => {
                const shelter = data.shelters.find((item) => item.id === need.shelter_id);
                return (
                  <div key={need.id} className="bg-zinc-950 border border-cyan-500/20 p-4 rounded-md flex justify-between items-center gap-3">
                    <div className="min-w-0">
                      <p className="text-lg font-bold text-white truncate">{need.item_type} x {need.requested_qty}</p>
                      <p className="text-sm text-zinc-500 truncate">{shelter?.name}</p>
                    </div>
                    <button
                      onClick={() => handleApprove(need.id)}
                      disabled={loading}
                      className="h-12 w-12 shrink-0 inline-flex items-center justify-center rounded-md bg-cyan-600 hover:bg-emerald-600 disabled:opacity-60"
                      title="Approve allocation"
                    >
                      <CheckCircle size={25} />
                    </button>
                  </div>
                );
              })}
              {pendingNeeds.length === 0 && <p className="text-zinc-600 text-base pt-8 text-center">All current needs are approved.</p>}
            </div>
          </section>

          <section className="min-w-0 overflow-y-auto custom-scrollbar">
            <h2 className="flex items-center gap-2 font-black text-sm tracking-widest mb-4 text-emerald-300 uppercase">
              <Truck size={22} /> Route Decisions
            </h2>
            <div className="space-y-3">
              {routeExplanations.map((route) => (
                <div key={route.id} className="bg-zinc-950 p-4 rounded-md border border-zinc-800">
                  <div className="flex justify-between gap-3 text-sm mb-2">
                    <span className={route.status === 'suggested' ? 'text-amber-300 font-bold truncate' : 'text-emerald-300 font-bold truncate'}>
                      {route.status === 'suggested' ? 'Suggested path' : 'Active dispatch'}
                    </span>
                    <span className="text-zinc-400 font-mono">{(route.distance / 1000).toFixed(1)} km</span>
                  </div>
                  <p className="text-base text-white truncate">{route.item_type} to {route.shelter_name}</p>
                  <p className="mt-2 text-sm leading-6 text-zinc-400">{route.route_explanation}</p>
                  <div className="mt-3 flex items-center justify-between gap-3 text-sm text-zinc-500">
                    <span>{Math.round(route.estimated_time / 60)} min ETA</span>
                    <span className={route.rerouted ? 'text-violet-300' : 'text-zinc-500'}>
                      {route.rerouted ? `avoids ${route.blocked_by_reason ?? route.blocked_by}` : 'direct optimized path'}
                    </span>
                  </div>
                </div>
              ))}
              {routeExplanations.length === 0 && <p className="text-zinc-600 text-base pt-8 text-center">Approve a need or inspect a suggested route to see optimization reasoning.</p>}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
}

function Metric({ icon: Icon, label, value, tone }) {
  return (
    <div className="flex items-center gap-3">
      <Icon size={26} className={tone} />
      <div>
        <p className="text-sm uppercase tracking-widest text-zinc-500">{label}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
      </div>
    </div>
  );
}

export default App;
