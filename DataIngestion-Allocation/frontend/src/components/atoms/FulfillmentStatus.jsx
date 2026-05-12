import React from 'react';

export function FulfillmentStatus({ fulfilled, done_by }) {
  if (fulfilled) {
    const name = done_by === 'us' ? 'ReliefGrid' : done_by;
    return (
      <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-accent-green/10 text-accent-green border border-accent-green/20 rounded text-xs font-mono font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-green"></span>
        Fulfilled by {name}
      </div>
    );
  }

  if (done_by) {
    return (
      <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-accent-amber/10 text-accent-amber border border-accent-amber/20 rounded text-xs font-mono font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-accent-amber animate-pulse"></span>
        In progress — {done_by}
      </div>
    );
  }

  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-accent-blue/10 text-accent-blue border border-accent-blue/20 rounded text-xs font-mono font-medium">
      <span className="w-1.5 h-1.5 rounded-full bg-accent-blue"></span>
      Open — needs volunteer
    </div>
  );
}
