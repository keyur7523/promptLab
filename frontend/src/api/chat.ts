/**
 * Chat API service with Server-Sent Events (SSE) streaming
 */

import type { StreamMetadata } from '../types';
import { API_BASE, getApiKey } from './config';

export interface StreamResult {
  token?: string;
  metadata?: StreamMetadata;
  error?: string;
}

/**
 * Stream chat response from backend using Server-Sent Events.
 *
 * @param message - User message
 * @param conversationId - Optional conversation ID for context
 * @param signal - Optional AbortSignal for cancellation
 * @yields Stream results containing tokens or metadata
 *
 * @example
 * ```ts
 * const controller = new AbortController();
 * for await (const result of streamChat("Hello!", conversationId, controller.signal)) {
 *   if (result.token) {
 *     console.log(result.token);
 *   } else if (result.metadata) {
 *     console.log("Done:", result.metadata);
 *   }
 * }
 * ```
 */
export async function* streamChat(
  message: string,
  conversationId?: string,
  signal?: AbortSignal
): AsyncGenerator<StreamResult> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': getApiKey(),
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
    }),
    signal,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`HTTP ${response.status}: ${error}`);
  }

  if (!response.body) {
    throw new Error('No response body');
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              yield { error: data.error };
              return;
            }

            if (data.token) {
              yield { token: data.token };
            }

            if (data.done) {
              yield { metadata: data as StreamMetadata };
              return;
            }
          } catch {
            // Skip malformed SSE data lines
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
