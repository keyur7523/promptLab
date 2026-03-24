import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import FeedbackButtons from '../FeedbackButtons';

vi.mock('../../api/feedback', () => ({
  submitFeedback: vi.fn(),
}));

import { submitFeedback } from '../../api/feedback';

describe('FeedbackButtons', () => {
  const mockSubmitFeedback = vi.mocked(submitFeedback);

  beforeEach(() => {
    mockSubmitFeedback.mockReset();
  });

  it('renders thumbs up and thumbs down buttons', () => {
    render(<FeedbackButtons messageId="msg-1" />);
    expect(screen.getByRole('button', { name: /helpful/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /unhelpful/i })).toBeInTheDocument();
  });

  it('submits positive feedback on thumbs up click', async () => {
    mockSubmitFeedback.mockResolvedValue(undefined);
    render(<FeedbackButtons messageId="msg-1" />);

    fireEvent.click(screen.getByRole('button', { name: /helpful/i }));

    await waitFor(() => {
      expect(mockSubmitFeedback).toHaveBeenCalledWith('msg-1', 1);
    });
  });

  it('shows confirmation text after voting', async () => {
    mockSubmitFeedback.mockResolvedValue(undefined);
    render(<FeedbackButtons messageId="msg-1" />);

    fireEvent.click(screen.getByRole('button', { name: /helpful/i }));

    await waitFor(() => {
      expect(screen.getByText('Thanks for your feedback!')).toBeInTheDocument();
    });
  });

  it('disables buttons after voting', async () => {
    mockSubmitFeedback.mockResolvedValue(undefined);
    render(<FeedbackButtons messageId="msg-1" />);

    fireEvent.click(screen.getByRole('button', { name: /helpful/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /helpful/i })).toBeDisabled();
      expect(screen.getByRole('button', { name: /unhelpful/i })).toBeDisabled();
    });
  });

  it('shows inline error message on failure instead of alert', async () => {
    mockSubmitFeedback.mockRejectedValue(new Error('Network error'));
    render(<FeedbackButtons messageId="msg-1" />);

    fireEvent.click(screen.getByRole('button', { name: /helpful/i }));

    await waitFor(() => {
      expect(screen.getByText('Failed to submit feedback. Please try again.')).toBeInTheDocument();
    });
  });
});
