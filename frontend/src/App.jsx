import React, { useState, useEffect } from 'react';
import axios from 'axios';
import DisasterMap from './components/Map';
import { Activity, Package, CheckCircle, RefreshCcw, Database, ShieldAlert, Truck } from 'lucide-react';

const API_BASE = "http://localhost:8000";

function App() {
  const [data, setData] = useState({ incidents: [], shelters: [], dispatches: [], need_cards: [], inventory: [] });
  const [newsInput, setNewsInput] = useState("");
  const [loading, setLoading] = useState(false);

  const loadAll = async () => {
    const res = await axios.get(`${API_BASE}/map-data`);
    setData(res.data);
  };

  useEffect(() => { loadAll(); }, []);

  const handleIngest = async () => {
    setLoading(true);
    await axios.post(`${API_BASE}/ingest`, { text: newsInput });
    setNewsInput("");
    setTimeout(loadAll, 2000); 
    setLoading(false);
  };

  const handleApprove = async (id) => {
    await axios.post(`${API_BASE}/allocate/approve/${id}`);
    loadAll();
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden font-sans">
      
      {/* SIDEBAR */}
      <div className="w-[380px] bg-slate-900 border-r border-slate-800 flex flex-col shadow-2xl z-10">
        <div className="p-6 border-b border-slate-800 flex justify-between items-center">
          <h1 className="text-xl font-black uppercase tracking-tighter italic flex items-center gap-2">
            <Activity className="text-blue-500" /> AEGIS AGENT
          </h1>
          <button onClick={() => axios.post(`${API_BASE}/system/reset`).then(loadAll)} className="text-red-500 hover:scale-110 transition-all"><ShieldAlert size={20}/></button>
        </div>

        <div className="p-6 space-y-6 flex-1 overflow-y-auto custom-scrollbar">
          {/* AI INPUT */}
          <section className="bg-slate-950 p-4 rounded-2xl border border-blue-500/20 shadow-xl">
            <h2 className="text-[10px] font-black uppercase text-blue-400 tracking-widest mb-4">01. Ingest News</h2>
            <textarea 
              className="w-full bg-slate-900 border border-slate-800 rounded-xl p-3 text-xs focus:ring-1 focus:ring-blue-500 outline-none h-24 resize-none"
              placeholder="Paste flood or landslide news here..."
              value={newsInput}
              onChange={(e) => setNewsInput(e.target.value)}
            />
            <button onClick={handleIngest} disabled={loading} className="w-full mt-3 bg-blue-600 hover:bg-blue-500 py-3 rounded-xl text-xs font-bold transition-all">
              {loading ? "Agent Processing..." : "Authorize AI Analysis"}
            </button>
          </section>

          {/* STOCK MONITOR */}
          <section>
            <h2 className="text-[10px] font-bold uppercase text-slate-500 tracking-widest mb-3">Inventory Levels</h2>
            <div className="space-y-2">
              {data.inventory?.map(inv => (
                <div key={inv.id} className="bg-slate-950/50 p-2 rounded-lg border border-slate-800 flex justify-between items-center">
                  <span className="text-[10px] text-slate-300">{inv.shelters?.name.split(' ')[0]}</span>
                  <span className="text-[10px] text-slate-500">{inv.item_name}</span>
                  <span className="text-xs font-mono font-bold text-blue-400">{inv.quantity}</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>

      {/* MAIN PANEL */}
      <div className="flex-1 flex flex-col">
        {/* Map Layer */}
        <div className="flex-1 relative">
          <DisasterMap data={data} />
        </div>

        {/* AGENT OUTPUT PANEL */}
        <div className="h-80 bg-slate-900 border-t border-slate-800 p-6 grid grid-cols-2 gap-8 shadow-2xl">
          
          {/* AUTO-GENERATED NEEDS */}
          <div className="border-r border-slate-800 pr-8 overflow-y-auto custom-scrollbar">
            <h2 className="flex items-center gap-2 font-black text-[11px] tracking-widest mb-4 text-blue-400 uppercase">
              <Database size={16}/> Agent Recommendations
            </h2>
            <div className="space-y-3">
              {data.need_cards?.filter(n => n.status === 'pending_approval').map(need => (
                <div key={need.id} className="bg-slate-950 border border-blue-500/30 p-4 rounded-xl flex justify-between items-center animate-pulse-once">
                  <div>
                    <p className="text-xs font-black text-blue-400 uppercase">New Incident Detected</p>
                    <p className="text-sm font-bold text-white mt-1">{need.item_type} x {need.requested_qty}</p>
                    <p className="text-[10px] text-slate-500 italic mt-1">Recommended Shelter: {data.shelters.find(s => s.id === need.shelter_id)?.name}</p>
                  </div>
                  <button onClick={() => handleApprove(need.id)} className="bg-blue-600 hover:bg-green-600 text-white p-3 rounded-full shadow-lg transition-all active:scale-90">
                    <CheckCircle size={24}/>
                  </button>
                </div>
              ))}
              {(!data.need_cards || data.need_cards.filter(n => n.status === 'pending_approval').length === 0) && (
                <p className="text-center text-slate-700 text-xs mt-10 italic">Awaiting AI Ingestion...</p>
              )}
            </div>
          </div>
          
          {/* ACTIVE DISPATCHES */}
          <div className="overflow-y-auto custom-scrollbar">
            <h2 className="flex items-center gap-2 font-black text-[11px] tracking-widest mb-4 text-amber-500 uppercase">
              <Truck size={16}/> Active Mission Status
            </h2>
            <div className="grid grid-cols-1 gap-3">
              {data.dispatches.map(d => (
                <div key={d.id} className="bg-slate-950 p-4 rounded-xl border border-amber-500/10">
                  <div className="flex justify-between items-center text-[10px] mb-3">
                    <span className="text-amber-500 font-black tracking-widest uppercase">Mission {d.id.slice(0,6)}</span>
                    <span className="text-slate-400">{(d.distance / 1000).toFixed(1)} KM</span>
                  </div>
                  <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                    <div className="bg-amber-500 h-full w-[45%] animate-pulse"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;