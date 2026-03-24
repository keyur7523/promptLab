/**
 * Modal for creating a new prompt version
 */

import { useState } from 'react';

interface PromptEditorProps {
  variant: string;
  currentContent: string;
  onSubmit: (content: string) => void;
  onCancel: () => void;
}

export default function PromptEditor({
  variant,
  currentContent,
  onSubmit,
  onCancel,
}: PromptEditorProps) {
  const [content, setContent] = useState(currentContent);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;
    onSubmit(content.trim());
  };

  const hasChanges = content.trim() !== currentContent.trim();

  return (
    <div className="experiment-form-overlay" onClick={onCancel}>
      <div className="experiment-form" onClick={(e) => e.stopPropagation()} style={{ width: '600px' }}>
        <h2>New Version for "{variant}"</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label>System Prompt</label>
            <textarea
              className="prompt-textarea"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              maxLength={5000}
              placeholder="Enter the system prompt..."
            />
            <div className="prompt-char-count">{content.length} / 5000</div>
          </div>

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onCancel}>
              Cancel
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={!content.trim() || !hasChanges}
            >
              Create Version
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
