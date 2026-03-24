/**
 * Prompts API client
 */

import type { PromptVersion } from '../types';
import { API_BASE, apiHeaders } from './config';

export async function listPrompts(): Promise<PromptVersion[]> {
  const res = await fetch(`${API_BASE}/prompts`, { headers: apiHeaders() });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function createPromptVersion(
  variant: string,
  content: string,
): Promise<PromptVersion> {
  const res = await fetch(`${API_BASE}/prompts`, {
    method: 'POST',
    headers: apiHeaders(),
    body: JSON.stringify({ variant, content }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function activatePromptVersion(id: string): Promise<PromptVersion> {
  const res = await fetch(`${API_BASE}/prompts/${id}/activate`, {
    method: 'PATCH',
    headers: apiHeaders(),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}
