import React from 'react';

export function LivePulse() {
  return (
    <div className="flex items-center gap-2">
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-red opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-red"></span>
      </span>
      <span className="text-xs font-mono font-bold text-accent-red uppercase tracking-wider">Live</span>
    </div>
  );
}
