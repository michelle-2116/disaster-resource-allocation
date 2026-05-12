import React from 'react';

const typeConfig = {
  send_food: { icon: '🍚', label: 'Food', classes: 'bg-accent-amber/10 text-accent-amber border-accent-amber/20' },
  send_meds: { icon: '💊', label: 'Medicine', classes: 'bg-accent-red/10 text-accent-red border-accent-red/20' },
  send_water: { icon: '💧', label: 'Water', classes: 'bg-accent-blue/10 text-accent-blue border-accent-blue/20' },
  send_rescue_team: { icon: '🚨', label: 'Rescue', classes: 'bg-accent-red/20 text-accent-red border-accent-red/30 font-extrabold' },
  reserve_resource: { icon: '📦', label: 'Resource', classes: 'bg-gray-100 text-gray-700 border-gray-200' },
};

export function NeedTypeBadge({ type }) {
  const config = typeConfig[type] || typeConfig.reserve_resource;
  
  return (
    <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded border text-xs font-bold uppercase tracking-wide ${config.classes}`}>
      <span>{config.icon}</span>
      <span>{config.label}</span>
    </div>
  );
}
