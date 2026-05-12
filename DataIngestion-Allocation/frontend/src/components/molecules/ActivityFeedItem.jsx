import React from 'react';
import { motion } from 'framer-motion';
import { Bot, UserCog, HeartHandshake, Server } from 'lucide-react';

const typeConfig = {
  agent: { color: 'border-accent-blue', bg: 'bg-accent-blue/10', icon: Bot, iconColor: 'text-accent-blue' },
  admin: { color: 'border-accent-green', bg: 'bg-accent-green/10', icon: UserCog, iconColor: 'text-accent-green' },
  volunteer: { color: 'border-accent-amber', bg: 'bg-accent-amber/10', icon: HeartHandshake, iconColor: 'text-accent-amber' },
  system: { color: 'border-gray-500', bg: 'bg-gray-800', icon: Server, iconColor: 'text-gray-400' },
};

function formatRelativeTime(isoString) {
  const diff = Math.floor((new Date() - new Date(isoString)) / 1000);
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

export function ActivityFeedItem({ activity }) {
  const config = typeConfig[activity.type] || typeConfig.system;
  const Icon = config.icon;

  return (
    <motion.div 
      layout
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-start gap-3 p-3 border-l-2 ${config.color} bg-[#1A1714] hover:bg-[#211E1A] transition-colors`}
    >
      <div className={`p-1.5 rounded-sm ${config.bg} ${config.iconColor} flex-shrink-0 mt-0.5`}>
        <Icon size={14} />
      </div>
      <div className="flex-grow min-w-0">
        <p className="text-sm text-gray-300 leading-snug">{activity.message}</p>
        <span className="text-[10px] text-gray-500 font-mono mt-1 block">
          {formatRelativeTime(activity.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}
