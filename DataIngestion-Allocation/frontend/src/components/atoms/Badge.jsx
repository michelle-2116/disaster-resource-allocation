import React from 'react';

const variantClasses = {
  critical: 'bg-accent-red text-white',
  high: 'bg-accent-amber text-white',
  medium: 'bg-yellow-500 text-white',
  low: 'bg-gray-500 text-white',
  fulfilled: 'bg-accent-green text-white',
  pending: 'bg-accent-amber text-white',
  open: 'bg-accent-blue text-white',
  approved: 'bg-accent-green text-white',
  in_progress: 'bg-accent-amber text-white',
};

export function Badge({ variant, label }) {
  return (
    <div className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider font-mono shadow-sm ${variantClasses[variant] || variantClasses.low}`}>
      {variant === 'pending' && (
        <span className="relative flex h-1.5 w-1.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-white"></span>
        </span>
      )}
      {label}
    </div>
  );
}
