import React, { useState } from 'react';
import { NeedTypeBadge } from '../atoms/NeedTypeBadge';
import { FulfillmentStatus } from '../atoms/FulfillmentStatus';

export function PublicNeedCard({ needCard, incidentName, onTakeUp, onDonate }) {
  const [expanded, setExpanded] = useState(false);

  const isFulfilled = needCard.fulfilled;
  const inProgress = needCard.done_by !== null && !isFulfilled;
  const isOpen = needCard.done_by === null && !isFulfilled;

  const cardClasses = `flex flex-col gap-4 p-5 rounded border bg-bg-card transition-all duration-200 
    ${isFulfilled ? 'opacity-60 grayscale-[0.5] border-gray-200' : 'border-border hover:border-gray-400 hover:shadow-sm'}`;

  return (
    <div className={cardClasses}>
      {/* Top row */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <NeedTypeBadge type={needCard.tool_name} />
          <span className="text-xs text-text-muted font-medium">{incidentName}</span>
        </div>
        <span className="text-xs text-text-muted font-mono">Just now</span>
      </div>

      {/* Main Content */}
      <div>
        <h3 className="text-xl font-bold font-serif text-text-primary">
          {needCard.quantity} × {needCard.item}
        </h3>
        
        <p 
          className={`mt-2 text-sm text-text-secondary cursor-pointer ${expanded ? '' : 'line-clamp-2'}`}
          onClick={() => setExpanded(!expanded)}
        >
          {needCard.explanation}
        </p>
      </div>

      {/* Warning Strip */}
      {needCard.note && (
        <div className="px-3 py-2 bg-accent-amber/10 border-l-2 border-accent-amber text-accent-amber text-xs font-bold flex items-center gap-2">
          <span>⚠</span>
          <span>{needCard.note}</span>
        </div>
      )}

      {/* Status Chip */}
      <div>
        <FulfillmentStatus fulfilled={isFulfilled} done_by={needCard.done_by} />
      </div>

      {/* Bottom Actions */}
      <div className="mt-auto pt-4 border-t border-border flex gap-3">
        {isOpen && (
          <button 
            onClick={() => onTakeUp(needCard)}
            className="w-full py-2 bg-accent-red text-white text-sm font-bold rounded shadow-sm hover:bg-red-700 transition-colors"
          >
            Take This Up
          </button>
        )}

        {inProgress && (
          <div className="flex-1 py-2 px-3 bg-accent-amber/10 text-accent-amber text-sm font-bold rounded text-center border border-accent-amber/20">
            Being handled by {needCard.done_by}
          </div>
        )}

        {isFulfilled && (
          <div className="flex-1 py-2 px-3 bg-gray-100 text-gray-500 text-sm font-bold rounded text-center border border-gray-200">
            Fulfilled
          </div>
        )}
      </div>
    </div>
  );
}
