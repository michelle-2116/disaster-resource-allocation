import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { NeedTypeBadge } from '../atoms/NeedTypeBadge';
import { FulfillmentStatus } from '../atoms/FulfillmentStatus';

export function ApprovalCard({ needCard, incidentName, onApprove, onDecline }) {
  const [actionState, setActionState] = useState(null); // null | 'approve' | 'decline'
  const [declineReason, setDeclineReason] = useState('AI over-allocated');

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
      className="bg-[#211E1A] border border-gray-800 rounded shadow-lg overflow-hidden flex flex-col"
    >
      {/* Pending Banner */}
      <div className="bg-accent-amber/20 px-5 py-2 border-b border-accent-amber/30 flex justify-between items-center">
        <span className="text-xs font-bold text-accent-amber uppercase tracking-wider flex items-center gap-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-amber opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-amber"></span>
          </span>
          Pending Approval
        </span>
        <span className="text-xs font-mono text-gray-400">ID: {needCard.id}</span>
      </div>

      <div className="p-5 flex flex-col gap-4 flex-grow">
        {/* Header */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-bold text-gray-300">{incidentName}</span>
          <NeedTypeBadge type={needCard.tool_name} />
        </div>

        {/* Title */}
        <div className="mb-4">
          <h3 className="text-2xl font-bold font-serif text-white">
            {needCard.quantity} × {needCard.item}
          </h3>
        </div>

        {/* AI Reasoning */}
        <div className="bg-[#1A1714] border border-gray-800 rounded p-3">
          <span className="text-[10px] font-bold text-accent-blue uppercase tracking-wider mb-1 block">
            AI Reasoning
          </span>
          <p className="text-sm text-gray-300">
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
          <FulfillmentStatus fulfilled={needCard.fulfilled} done_by={needCard.done_by} />
        </div>

        <div className="mt-auto pt-4 border-t border-gray-800 relative overflow-hidden min-h-[100px]">
          <AnimatePresence mode="wait">
            {!actionState && (
              <motion.div 
                key="default"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="space-y-3"
              >
                <p className="text-[10px] text-gray-500 uppercase tracking-wider text-center">
                  Approving makes this visible to volunteers on the public dashboard.
                </p>
                <div className="flex gap-3">
                  <button 
                    onClick={() => setActionState('decline')}
                    className="flex-1 py-2 bg-transparent border border-gray-600 text-gray-300 text-sm font-bold rounded hover:bg-gray-800 transition-colors"
                  >
                    Don't Publish
                  </button>
                  <button 
                    onClick={() => setActionState('approve')}
                    className="flex-1 py-2 bg-accent-green text-white text-sm font-bold rounded shadow-sm hover:bg-green-700 transition-colors"
                  >
                    Publish to Dashboard
                  </button>
                </div>
              </motion.div>
            )}

            {actionState === 'approve' && (
              <motion.div 
                key="approve"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex flex-col gap-3 h-full justify-center"
              >
                <p className="text-sm text-center text-white font-medium">
                  This need will be visible to volunteers and donors. Confirm?
                </p>
                <div className="flex gap-3 mt-auto">
                  <button 
                    onClick={() => setActionState(null)}
                    className="flex-1 py-2 bg-transparent border border-gray-600 text-gray-300 text-sm font-bold rounded hover:bg-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={() => onApprove(needCard)}
                    className="flex-1 py-2 bg-accent-green text-white text-sm font-bold rounded shadow-sm hover:bg-green-700 transition-colors"
                  >
                    Confirm Publish
                  </button>
                </div>
              </motion.div>
            )}

            {actionState === 'decline' && (
              <motion.div 
                key="decline"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="flex flex-col gap-3 h-full justify-center"
              >
                <select 
                  value={declineReason}
                  onChange={e => setDeclineReason(e.target.value)}
                  className="w-full px-3 py-2 bg-[#1A1714] border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-accent-amber"
                >
                  <option>AI over-allocated</option>
                  <option>Duplicate</option>
                  <option>Already handled</option>
                  <option>Needs review</option>
                </select>
                <div className="flex gap-3 mt-auto">
                  <button 
                    onClick={() => setActionState(null)}
                    className="flex-1 py-2 bg-transparent border border-gray-600 text-gray-300 text-sm font-bold rounded hover:bg-gray-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button 
                    onClick={() => onDecline(needCard, declineReason)}
                    className="flex-1 py-2 bg-gray-700 text-white text-sm font-bold rounded shadow-sm hover:bg-gray-600 transition-colors"
                  >
                    Confirm Decline
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
