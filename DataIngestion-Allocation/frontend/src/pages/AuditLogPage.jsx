import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ActivityFeed, Skeleton } from '../components';
import { usePageTitle } from '../hooks/usePageTitle';

export default function AuditLogPage() {
  usePageTitle('Audit Log');
  const [loading, setLoading] = useState(true);
  const [feedItems, setFeedItems] = useState([]);

  useEffect(() => {
    const fetchFeed = async () => {
      setLoading(true);
      const res = await api.getActivityFeed();
      if (res.data) setFeedItems(res.data);
      setLoading(false);
    };
    fetchFeed();
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h2 className="text-3xl font-bold tracking-tight text-text-primary mb-2">Comprehensive Audit Log</h2>
        <p className="text-sm text-text-secondary">
          A complete historical record of all agent decisions, admin approvals, and volunteer interactions.
        </p>
      </div>

      <div className="bg-bg-card border border-border rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-6">
            <Skeleton height="h-[600px]" />
          </div>
        ) : (
          <ActivityFeed items={feedItems} maxHeight="max-h-[800px]" />
        )}
      </div>
    </div>
  );
}
