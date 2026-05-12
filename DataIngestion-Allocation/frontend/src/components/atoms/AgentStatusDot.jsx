import React from 'react';

const statusConfig = {
  active: { color: 'bg-accent-green', text: 'Online', pulse: true },
  idle: { color: 'bg-gray-500', text: 'Idle', pulse: false },
  error: { color: 'bg-accent-red', text: 'Error', pulse: true },
};

export function AgentStatusDot({ agentName, status = 'idle' }) {
  const config = statusConfig[status] || statusConfig.idle;

  return (
    <div className="flex items-center justify-between py-1">
      <span className="text-sm text-gray-300">{agentName}</span>
      <div className="flex items-center gap-1.5">
        {config.pulse ? (
          <span className="relative flex h-2 w-2">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${config.color} opacity-75`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${config.color}`}></span>
          </span>
        ) : (
          <span className={`w-2 h-2 rounded-full ${config.color}`}></span>
        )}
        <span className="text-xs font-mono text-gray-400">{config.text}</span>
      </div>
    </div>
  );
}
