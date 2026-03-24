/**
 * Conversations API client
 */

import type { ConversationSummary, ConversationMessage } from '../types';
import { API_BASE, getApiKey } from './config';

export async function listConversations(
  limit = 20,
  offset = 0,
): Promise<{ conversations: ConversationSummary[]; total: number }> {
  const res = await fetch(
    `${API_BASE}/conversations?limit=${limit}&offset=${offset}`,
    { headers: { 'x-api-key': getApiKey() } },
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  return res.json();
}

export async function getConversationMessages(
  id: string,
): Promise<ConversationMessage[]> {
  const res = await fetch(`${API_BASE}/conversations/${id}/messages`, {
    headers: { 'x-api-key': getApiKey() },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
  const data = await res.json();
  return data.messages;
}

export async function deleteConversation(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/conversations/${id}`, {
    method: 'DELETE',
    headers: { 'x-api-key': getApiKey() },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
}
