/**
 * Main chat component with streaming support and conversation sidebar
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type { Message } from '../types';
import { streamChat } from '../api/chat';
import { getConversationMessages } from '../api/conversations';
import MessageList from './MessageList';
import ConversationSidebar from './ConversationSidebar';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [showDevInfo, setShowDevInfo] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Cancel any in-flight stream on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleNewChat = useCallback(() => {
    abortControllerRef.current?.abort();
    setMessages([]);
    setConversationId(undefined);
    setIsStreaming(false);
    setInput('');
  }, []);

  const handleSelectConversation = useCallback(async (id: string) => {
    if (id === conversationId) return;
    abortControllerRef.current?.abort();
    setIsStreaming(false);

    try {
      const msgs = await getConversationMessages(id);
      setMessages(
        msgs
          .filter((m) => m.role !== 'system')
          .map((m) => ({
            id: m.id,
            role: m.role as 'user' | 'assistant',
            content: m.content,
            variant: m.variant,
            model: m.model,
            tokens_in: m.tokens_in,
            tokens_out: m.tokens_out,
            latency_ms: m.latency_ms,
            cost: m.cost ?? undefined,
            timestamp: new Date(m.created_at),
          })),
      );
      setConversationId(id);
    } catch {
      // Failed to load — keep current state
    }
  }, [conversationId]);

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

    const tempId = crypto.randomUUID();
    const assistantMessage: Message = {
      id: tempId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, assistantMessage]);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      let fullContent = '';

      for await (const result of streamChat(userMessage.content, conversationId, controller.signal)) {
        if (result.error) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: `Error: ${result.error}`,
            };
            return updated;
          });
          break;
        }

        if (result.token) {
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
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              id: result.metadata!.message_id,
              variant: result.metadata!.variant,
              model: result.metadata!.model,
              tokens_in: result.metadata!.tokens_in,
              tokens_out: result.metadata!.tokens_out,
              latency_ms: result.metadata!.latency_ms,
              cost: result.metadata!.cost,
            };
            return updated;
          });

          if (!conversationId) {
            setConversationId(result.metadata.conversation_id);
          }
        }
      }
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        return;
      }
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        };
        return updated;
      });
    } finally {
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, [input, isStreaming, conversationId]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-layout">
      {showSidebar && (
        <ConversationSidebar
          currentConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewChat={handleNewChat}
        />
      )}

      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="chat-header__left">
            <button
              className="sidebar-toggle"
              onClick={() => setShowSidebar(!showSidebar)}
              title={showSidebar ? 'Hide history' : 'Show history'}
              aria-label="Toggle conversation history"
            >
              {showSidebar ? '\u2715' : '\u2630'}
            </button>
            <h1>PromptLab</h1>
          </div>
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
                {conversationId.slice(0, 8)}...
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
            onKeyDown={handleKeyDown}
            placeholder="Type your message... (Enter to send, Shift+Enter for new line)"
            disabled={isStreaming}
            rows={3}
            aria-label="Chat message input"
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
    </div>
  );
}
