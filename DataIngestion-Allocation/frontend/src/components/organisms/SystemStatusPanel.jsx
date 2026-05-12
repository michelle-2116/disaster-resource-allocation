import React from 'react';
import { AgentStatusDot } from '../atoms/AgentStatusDot';

export function SystemStatusPanel({ pendingCount = 0, openNeedsCount = 0, lastSync = 'Just now' }) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-col gap-1">
        <AgentStatusDot agentName="Verification Agent" status="online" />
        <AgentStatusDot agentName="Allocation Agent" status="online" />
      </div>
      
      <div className="grid grid-cols-2 gap-2 mt-2 pt-4 border-t border-gray-800">
        <div className="bg-[#1A1714] p-2 rounded border border-gray-800 text-center">
          <div className="text-xl font-mono font-bold text-accent-amber">{pendingCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold mt-1">Pending</div>
        </div>
        <div className="bg-[#1A1714] p-2 rounded border border-gray-800 text-center">
          <div className="text-xl font-mono font-bold text-accent-blue">{openNeedsCount}</div>
          <div className="text-[10px] text-gray-500 uppercase tracking-wider font-bold mt-1">Open Needs</div>
        </div>
      </div>
      
      <div className="text-center mt-2">
        <span className="text-xs text-gray-500 font-mono">Last sync: {lastSync}</span>
      </div>
    </div>
  );
}
