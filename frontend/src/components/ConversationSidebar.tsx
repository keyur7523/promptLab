/**
 * Sidebar listing past conversations with load/delete actions
 */

import { useState, useEffect, useCallback } from 'react';
import type { ConversationSummary } from '../types';
import { listConversations, deleteConversation } from '../api/conversations';
import ConfirmDialog from './ConfirmDialog';

interface ConversationSidebarProps {
  currentConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewChat: () => void;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function ConversationSidebar({
  currentConversationId,
  onSelectConversation,
  onNewChat,
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const fetchConversations = useCallback(async () => {
    try {
      const data = await listConversations(50);
      setConversations(data.conversations);
    } catch {
      // Silently fail — sidebar is non-critical
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConversations();
  }, [fetchConversations, currentConversationId]);

  const handleDeleteClick = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setDeleteTarget(id);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteConversation(deleteTarget);
      setConversations((prev) => prev.filter((c) => c.id !== deleteTarget));
      if (deleteTarget === currentConversationId) {
        onNewChat();
      }
    } catch {
      // Silently fail
    } finally {
      setDeleteTarget(null);
    }
  };

  return (
    <div className="sidebar">
      <div className="sidebar__header">
        <span className="sidebar__title">History</span>
        <button className="btn-primary sidebar__new-btn" onClick={onNewChat}>
          + New
        </button>
      </div>

      <div className="sidebar__list">
        {loading ? (
          <div className="sidebar__loading">Loading...</div>
        ) : conversations.length === 0 ? (
          <div className="sidebar__empty">No conversations yet</div>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              className={`sidebar__item ${conv.id === currentConversationId ? 'sidebar__item--active' : ''}`}
              onClick={() => onSelectConversation(conv.id)}
            >
              <div className="sidebar__item-preview">
                {conv.preview || 'Empty conversation'}
              </div>
              <div className="sidebar__item-meta">
                <span>{formatDate(conv.created_at)}</span>
                <span>{conv.message_count} msgs</span>
                <button
                  className="sidebar__delete-btn"
                  onClick={(e) => handleDeleteClick(e, conv.id)}
                  title="Delete conversation"
                >
                  x
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {deleteTarget && (
        <ConfirmDialog
          message="Delete this conversation?"
          onConfirm={confirmDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
