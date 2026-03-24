/**
 * Analytics API client
 */

import type {
  AnalyticsOverview,
  UsageDataPoint,
  ExperimentStats,
  LatencyBucket,
} from '../types';
import { API_BASE, getApiKey } from './config';

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'x-api-key': getApiKey() },
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

export async function getOverview(days = 7): Promise<AnalyticsOverview> {
  return fetchJson<AnalyticsOverview>(`/analytics/overview?days=${days}`);
}

export async function getUsage(days = 7): Promise<UsageDataPoint[]> {
  const data = await fetchJson<{ usage: UsageDataPoint[] }>(`/analytics/usage?days=${days}`);
  return data.usage;
}

export async function getExperiments(): Promise<ExperimentStats[]> {
  const data = await fetchJson<{ experiments: ExperimentStats[] }>('/analytics/experiments');
  return data.experiments;
}

export async function getLatencyDistribution(): Promise<LatencyBucket[]> {
  const data = await fetchJson<{ distribution: LatencyBucket[] }>('/analytics/latency');
  return data.distribution;
}
