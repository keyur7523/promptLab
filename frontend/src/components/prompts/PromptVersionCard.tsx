/**
 * Card displaying a single prompt version
 */

import type { PromptVersion } from '../../types';

interface PromptVersionCardProps {
  prompt: PromptVersion;
  onActivate: (id: string) => void;
  onCompare: (prompt: PromptVersion) => void;
  isComparing: boolean;
}

export default function PromptVersionCard({
  prompt,
  onActivate,
  onCompare,
  isComparing,
}: PromptVersionCardProps) {
  const date = new Date(prompt.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className={`prompt-card ${prompt.is_active ? 'prompt-card--active' : ''}`}>
      <div className="prompt-card__header">
        <div className="prompt-card__version">
          v{prompt.version}
          {prompt.is_active && <span className="prompt-card__active-badge">Active</span>}
        </div>
        <div className="prompt-card__actions">
          <button
            className={`btn-text ${isComparing ? 'btn-text--selected' : ''}`}
            onClick={() => onCompare(prompt)}
          >
            {isComparing ? 'Selected' : 'Compare'}
          </button>
          {!prompt.is_active && (
            <button className="btn-text" onClick={() => onActivate(prompt.id)}>
              Activate
            </button>
          )}
        </div>
      </div>
      <pre className="prompt-card__content">{prompt.content}</pre>
      <div className="prompt-card__date">{date}</div>
    </div>
  );
}
