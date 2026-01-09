/**
 * Main chat component with streaming support
 */

import { useState, useCallback } from 'react';
import type { Message } from '../types';
import { streamChat } from '../api/chat';
import MessageList from './MessageList';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [showDevInfo, setShowDevInfo] = useState(false);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isStreaming) return;

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsStreaming(true);

    // Create placeholder for assistant message
    const assistantMessage: Message = {
      id: '',
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    try {
      let fullContent = '';

      for await (const result of streamChat(userMessage.content, conversationId)) {
        if (result.error) {
          // Handle error
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: `❌ Error: ${result.error}`,
            };
            return updated;
          });
          break;
        }

        if (result.token) {
          // Append token to content
          fullContent += result.token;

          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: fullContent,
            };
            return updated;
          });
        }

        if (result.metadata) {
          // Update with final metadata
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              id: result.metadata!.message_id,
              variant: result.metadata!.variant,
              model: result.metadata!.model,
            };
            return updated;
          });

          // Set conversation ID if not already set
          if (!conversationId) {
            setConversationId(result.metadata.conversation_id);
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        };
        return updated;
      });
    } finally {
      setIsStreaming(false);
    }
  }, [input, isStreaming, conversationId]);

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-container">
      {/* Header */}
      <div className="chat-header">
        <h1>AI Chat Platform</h1>
        <div className="header-controls">
          <label className="dev-mode-toggle">
            <input
              type="checkbox"
              checked={showDevInfo}
              onChange={(e) => setShowDevInfo(e.target.checked)}
            />
            <span>Dev Mode</span>
          </label>
          {conversationId && (
            <span className="conversation-id" title={conversationId}>
              Conversation: {conversationId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {/* Message list */}
      <MessageList messages={messages} showDevInfo={showDevInfo} />

      {/* Input area */}
      <div className="input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
          disabled={isStreaming}
          rows={3}
        />
        <button
          onClick={handleSend}
          disabled={isStreaming || !input.trim()}
          className="send-button"
        >
          {isStreaming ? '...' : 'Send'}
        </button>
      </div>

      {/* Status bar */}
      {isStreaming && (
        <div className="status-bar">
          <span className="streaming-indicator">● Streaming response...</span>
        </div>
      )}
    </div>
  );
}
