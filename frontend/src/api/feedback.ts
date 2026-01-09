/**
 * Feedback API service
 */

import type { FeedbackRequest } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key-12345';

/**
 * Submit feedback (thumbs up/down) for an assistant message.
 *
 * @param messageId - ID of the assistant message
 * @param rating - 1 for thumbs up, -1 for thumbs down
 * @param comment - Optional comment
 */
export async function submitFeedback(
  messageId: string,
  rating: 1 | -1,
  comment?: string
): Promise<void> {
  const response = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
    },
    body: JSON.stringify({
      message_id: messageId,
      rating,
      comment,
    } as FeedbackRequest),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Failed to submit feedback: ${error}`);
  }
}
