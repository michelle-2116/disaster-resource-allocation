import React from 'react';
import { AnimatePresence } from 'framer-motion';
import { ActivityFeedItem } from '../molecules/ActivityFeedItem';
import { LivePulse } from '../atoms/LivePulse';

export function ActivityFeed({ items, maxHeight = 'max-h-[400px]' }) {
  return (
    <div className="flex flex-col bg-[#211E1A] border border-gray-800 rounded overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-800 flex justify-between items-center bg-[#1A1714]">
        <h3 className="font-bold text-white flex items-center gap-2">
          System Log
        </h3>
        <LivePulse />
      </div>
      
      <div className={`overflow-y-auto ${maxHeight} p-2 space-y-1`}>
        <AnimatePresence>
          {items.map((activity) => (
            <ActivityFeedItem key={activity.id} activity={activity} />
          ))}
        </AnimatePresence>
        
        {items.length === 0 && (
          <div className="p-4 text-center text-gray-500 text-sm">
            No recent activity.
          </div>
        )}
      </div>
    </div>
  );
}
