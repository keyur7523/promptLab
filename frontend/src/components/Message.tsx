/**
 * Individual message component
 */

import type { Message as MessageType } from '../types';
import FeedbackButtons from './FeedbackButtons';

interface MessageProps {
  message: MessageType;
  showDevInfo?: boolean;
}

function formatCost(cost: number): string {
  if (cost < 0.0001) return '<$0.0001';
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(3)}`;
}

function TokenStats({ message }: { message: MessageType }) {
  const hasStats = message.tokens_in || message.tokens_out || message.latency_ms;
  if (!hasStats) return null;

  const totalTokens = (message.tokens_in || 0) + (message.tokens_out || 0);

  return (
    <div className="token-stats">
      <div className="token-stats-row">
        {message.tokens_in !== undefined && (
          <div className="token-stat">
            <span className="token-stat-icon">↓</span>
            <span className="token-stat-value">{message.tokens_in}</span>
            <span className="token-stat-label">in</span>
          </div>
        )}
        {message.tokens_out !== undefined && (
          <div className="token-stat">
            <span className="token-stat-icon">↑</span>
            <span className="token-stat-value">{message.tokens_out}</span>
            <span className="token-stat-label">out</span>
          </div>
        )}
        {totalTokens > 0 && (
          <div className="token-stat total">
            <span className="token-stat-icon">Σ</span>
            <span className="token-stat-value">{totalTokens}</span>
            <span className="token-stat-label">tokens</span>
          </div>
        )}
        {message.latency_ms !== undefined && (
          <div className="token-stat latency">
            <span className="token-stat-icon">⚡</span>
            <span className="token-stat-value">{(message.latency_ms / 1000).toFixed(1)}s</span>
          </div>
        )}
        {message.cost !== undefined && message.cost > 0 && (
          <div className="token-stat cost">
            <span className="token-stat-icon">💰</span>
            <span className="token-stat-value">{formatCost(message.cost)}</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Message({ message, showDevInfo = false }: MessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`message ${isUser ? 'user-message' : 'assistant-message'}`}>
      <div className="message-role">
        {isUser ? '👤 You' : '🤖 Assistant'}
      </div>
      <div className="message-content">
        {message.content}
      </div>

      {/* Token stats for assistant messages */}
      {!isUser && <TokenStats message={message} />}

      {/* Show feedback buttons only for assistant messages with IDs */}
      {!isUser && message.id && (
        <FeedbackButtons messageId={message.id} />
      )}

      {/* Developer info (variant, model) */}
      {showDevInfo && !isUser && (message.variant || message.model) && (
        <div className="message-metadata">
          {message.variant && <span className="badge">Variant: {message.variant}</span>}
          {message.model && <span className="badge">Model: {message.model}</span>}
        </div>
      )}
    </div>
  );
}
