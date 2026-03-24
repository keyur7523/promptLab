/**
 * API key management client
 */

import type { ApiKeyInfo } from '../types';
import { API_BASE, apiHeaders } from './config';

export async function getKeyInfo(): Promise<ApiKeyInfo> {
  const res = await fetch(`${API_BASE}/api-keys/me`, { headers: apiHeaders() });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function rotateKey(): Promise<{ api_key: string }> {
  const res = await fetch(`${API_BASE}/api-keys/rotate`, {
    method: 'POST',
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function generateNewKey(): Promise<{ api_key: string; user_id: string }> {
  const res = await fetch(`${API_BASE}/api-keys/generate`, {
    method: 'POST',
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export function getExportUrl(type: 'experiments' | 'conversations', days?: number): string {
  const base = `${API_BASE}/export/${type}`;
  return days ? `${base}?days=${days}` : base;
}
