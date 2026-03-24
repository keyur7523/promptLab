/**
 * Feedback API service
 */

import type { FeedbackRequest } from '../types';
import { API_BASE, getApiKey } from './config';

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
      'x-api-key': getApiKey(),
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
