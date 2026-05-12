import { useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for polling data at regular intervals.
 * 
 * @param {Function} fetchFn - Async function that fetches data
 * @param {number} interval - Poll interval in milliseconds (from VITE_POLL_INTERVAL_MS env)
 * @param {boolean} enabled - Whether polling is enabled (default: true)
 * @param {Array} deps - Additional dependencies for the effect
 */
export function usePolling(fetchFn, interval = 30000, enabled = true, deps = []) {
  const intervalRef = useRef(null);
  const fetchFnRef = useRef(fetchFn);

  // Update ref when fetchFn changes
  useEffect(() => {
    fetchFnRef.current = fetchFn;
  }, [fetchFn]);

  useEffect(() => {
    if (!enabled) {
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    // Poll immediately on mount
    fetchFnRef.current();

    // Then set up interval polling
    intervalRef.current = setInterval(() => {
      fetchFnRef.current();
    }, interval);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [interval, enabled, ...deps]);

  return { isPolling: enabled };
}
