/**
 * Message list component with auto-scroll
 */

import { useEffect, useRef } from 'react';
import type { Message as MessageType } from '../types';
import Message from './Message';

interface MessageListProps {
  messages: MessageType[];
  showDevInfo?: boolean;
}

export default function MessageList({ messages, showDevInfo }: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="message-list">
      {messages.length === 0 && (
        <div className="empty-state">
          <h2>👋 Welcome to AI Chat</h2>
          <p>Start a conversation by typing a message below.</p>
        </div>
      )}

      {messages.map((message, index) => (
        <Message
          key={message.id || `temp-${index}`}
          message={message}
          showDevInfo={showDevInfo}
        />
      ))}

      {/* Invisible div for auto-scrolling */}
      <div ref={messagesEndRef} />
    </div>
  );
}
