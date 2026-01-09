/**
 * Feedback buttons component (thumbs up/down)
 */

import { useState } from 'react';
import { submitFeedback } from '../api/feedback';

interface FeedbackButtonsProps {
  messageId: string;
}

export default function FeedbackButtons({ messageId }: FeedbackButtonsProps) {
  const [voted, setVoted] = useState<1 | -1 | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleVote = async (rating: 1 | -1) => {
    if (voted || isSubmitting) return;

    setIsSubmitting(true);

    try {
      await submitFeedback(messageId, rating);
      setVoted(rating);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="feedback-buttons">
      <button
        onClick={() => handleVote(1)}
        disabled={voted !== null || isSubmitting}
        className={`feedback-btn ${voted === 1 ? 'active' : ''}`}
        title="Thumbs up"
      >
        👍
      </button>
      <button
        onClick={() => handleVote(-1)}
        disabled={voted !== null || isSubmitting}
        className={`feedback-btn ${voted === -1 ? 'active' : ''}`}
        title="Thumbs down"
      >
        👎
      </button>
      {voted && <span className="voted-text">Thanks for your feedback!</span>}
    </div>
  );
}
