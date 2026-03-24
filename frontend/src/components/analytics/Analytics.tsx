/**
 * Analytics dashboard page
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  AnalyticsOverview,
  UsageDataPoint,
  ExperimentStats,
  LatencyBucket,
} from '../../types';
import { getOverview, getUsage, getExperiments, getLatencyDistribution } from '../../api/analytics';
import OverviewCards from './OverviewCards';
import UsageChart from './UsageChart';
import ExperimentTable from './ExperimentTable';
import LatencyChart from './LatencyChart';

type TimeRange = 7 | 14 | 30;

export default function Analytics() {
  const [days, setDays] = useState<TimeRange>(7);
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [usage, setUsage] = useState<UsageDataPoint[]>([]);
  const [experiments, setExperiments] = useState<ExperimentStats[]>([]);
  const [latency, setLatency] = useState<LatencyBucket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async (range: TimeRange) => {
    setLoading(true);
    setError(null);
    try {
      const [overviewData, usageData, experimentsData, latencyData] = await Promise.all([
        getOverview(range),
        getUsage(range),
        getExperiments(),
        getLatencyDistribution(),
      ]);
      setOverview(overviewData);
      setUsage(usageData);
      setExperiments(experimentsData);
      setLatency(latencyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(days);
  }, [days, fetchData]);

  return (
    <div className="analytics-container">
      <div className="analytics-header">
        <h1>Analytics</h1>
        <div className="analytics-controls">
          {([7, 14, 30] as TimeRange[]).map((range) => (
            <button
              key={range}
              className={`range-btn ${days === range ? 'active' : ''}`}
              onClick={() => setDays(range)}
            >
              {range}d
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="analytics-error">
          {error}
        </div>
      )}

      {loading ? (
        <div className="analytics-loading">Loading analytics...</div>
      ) : (
        <>
          {overview && <OverviewCards data={overview} />}
          <div className="analytics-charts-grid">
            <UsageChart data={usage} />
            <LatencyChart data={latency} />
          </div>
          <ExperimentTable data={experiments} />
        </>
      )}
    </div>
  );
}
