/**
 * Experiments API client
 */

import type { Experiment, ExperimentCreateRequest, ExperimentUpdateRequest } from '../types';
import { API_BASE, apiHeaders } from './config';

export async function listExperiments(): Promise<Experiment[]> {
  const res = await fetch(`${API_BASE}/experiments`, { headers: apiHeaders() });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function createExperiment(data: ExperimentCreateRequest): Promise<Experiment> {
  const res = await fetch(`${API_BASE}/experiments`, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function updateExperiment(id: string, data: ExperimentUpdateRequest): Promise<Experiment> {
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'PATCH',
    headers: apiHeaders(),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function deleteExperiment(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/experiments/${id}`, {
    method: 'DELETE',
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
}
