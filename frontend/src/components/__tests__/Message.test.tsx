import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import Message from '../Message';
import type { Message as MessageType } from '../../types';

describe('Message', () => {
  const userMessage: MessageType = {
    id: 'msg-1',
    role: 'user',
    content: 'Hello, how are you?',
  };

  const assistantMessage: MessageType = {
    id: 'msg-2',
    role: 'assistant',
    content: 'I am doing well, thanks!',
    variant: 'concise',
    model: 'gpt-4',
    tokens_in: 10,
    tokens_out: 25,
    latency_ms: 1500,
    cost: 0.0023,
  };

  it('renders user message with correct role label', () => {
    render(<Message message={userMessage} />);
    expect(screen.getByText('You', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
  });

  it('renders assistant message with correct role label', () => {
    render(<Message message={assistantMessage} />);
    expect(screen.getByText('Assistant', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('I am doing well, thanks!')).toBeInTheDocument();
  });

  it('shows token stats for assistant messages', () => {
    render(<Message message={assistantMessage} />);
    expect(screen.getByText('10')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('35')).toBeInTheDocument();
  });

  it('does not show token stats for user messages', () => {
    render(<Message message={userMessage} />);
    expect(screen.queryByText('tokens')).not.toBeInTheDocument();
  });

  it('shows feedback buttons for assistant messages', () => {
    render(<Message message={assistantMessage} />);
    expect(screen.getByRole('button', { name: /helpful/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /unhelpful/i })).toBeInTheDocument();
  });

  it('does not show feedback buttons for user messages', () => {
    render(<Message message={userMessage} />);
    expect(screen.queryByRole('button', { name: /helpful/i })).not.toBeInTheDocument();
  });

  it('shows dev info when showDevInfo is true', () => {
    render(<Message message={assistantMessage} showDevInfo={true} />);
    expect(screen.getByText('Variant: concise')).toBeInTheDocument();
    expect(screen.getByText('Model: gpt-4')).toBeInTheDocument();
  });

  it('hides dev info when showDevInfo is false', () => {
    render(<Message message={assistantMessage} showDevInfo={false} />);
    expect(screen.queryByText('Variant: concise')).not.toBeInTheDocument();
    expect(screen.queryByText('Model: gpt-4')).not.toBeInTheDocument();
  });
});
