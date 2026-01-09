/**
 * Individual message component
 */

import type { Message as MessageType } from '../types';
import FeedbackButtons from './FeedbackButtons';

interface MessageProps {
  message: MessageType;
  showDevInfo?: boolean;
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
