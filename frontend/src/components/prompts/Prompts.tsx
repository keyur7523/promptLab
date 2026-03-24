/**
 * Prompt version registry page
 */

import { useState, useEffect, useCallback } from 'react';
import type { PromptVersion } from '../../types';
import { listPrompts, createPromptVersion, activatePromptVersion } from '../../api/prompts';
import PromptVersionCard from './PromptVersionCard';
import PromptEditor from './PromptEditor';
import PromptDiff from './PromptDiff';

export default function Prompts() {
  const [allPrompts, setAllPrompts] = useState<PromptVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeVariant, setActiveVariant] = useState<string | null>(null);
  const [showEditor, setShowEditor] = useState(false);
  const [compareSelection, setCompareSelection] = useState<PromptVersion[]>([]);
  const [showDiff, setShowDiff] = useState(false);

  const fetchPrompts = useCallback(async () => {
    try {
      const data = await listPrompts();
      setAllPrompts(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load prompts');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPrompts();
  }, [fetchPrompts]);

  // Group prompts by variant
  const variants = Array.from(new Set(allPrompts.map((p) => p.variant))).sort();
  const currentVariant = activeVariant ?? variants[0] ?? null;
  const variantPrompts = allPrompts
    .filter((p) => p.variant === currentVariant)
    .sort((a, b) => b.version - a.version);

  const activePrompt = variantPrompts.find((p) => p.is_active);

  const handleCreate = async (content: string) => {
    if (!currentVariant) return;
    try {
      await createPromptVersion(currentVariant, content);
      setShowEditor(false);
      await fetchPrompts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create version');
    }
  };

  const handleActivate = async (id: string) => {
    try {
      await activatePromptVersion(id);
      await fetchPrompts();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate version');
    }
  };

  const handleCompare = (prompt: PromptVersion) => {
    setCompareSelection((prev) => {
      const exists = prev.find((p) => p.id === prompt.id);
      if (exists) return prev.filter((p) => p.id !== prompt.id);
      if (prev.length >= 2) return [prev[1], prompt];
      return [...prev, prompt];
    });
  };

  useEffect(() => {
    if (compareSelection.length === 2) {
      setShowDiff(true);
    }
  }, [compareSelection]);

  const handleCloseDiff = () => {
    setShowDiff(false);
    setCompareSelection([]);
  };

  return (
    <div className="experiments-container">
      <div className="experiments-header">
        <div>
          <h1>Prompt Registry</h1>
          <p className="experiments-subtitle">
            {variants.length} variant{variants.length !== 1 ? 's' : ''} &middot; {allPrompts.length} version{allPrompts.length !== 1 ? 's' : ''} total
          </p>
        </div>
        {currentVariant && (
          <button className="btn-primary" onClick={() => setShowEditor(true)}>
            + New Version
          </button>
        )}
      </div>

      {error && <div className="analytics-error">{error}</div>}

      {/* Variant tabs */}
      {variants.length > 0 && (
        <div className="prompt-tabs">
          {variants.map((v) => (
            <button
              key={v}
              className={`prompt-tab ${v === currentVariant ? 'prompt-tab--active' : ''}`}
              onClick={() => {
                setActiveVariant(v);
                setCompareSelection([]);
              }}
            >
              {v}
            </button>
          ))}
        </div>
      )}

      {compareSelection.length > 0 && compareSelection.length < 2 && (
        <div className="prompt-compare-hint">
          Select one more version to compare
        </div>
      )}

      {loading ? (
        <div className="analytics-loading">Loading prompts...</div>
      ) : variants.length === 0 ? (
        <div className="experiments-empty">
          <p>No prompt versions yet. Prompts use hardcoded defaults until you create versions here.</p>
        </div>
      ) : (
        <div className="prompt-list">
          {variantPrompts.map((p) => (
            <PromptVersionCard
              key={p.id}
              prompt={p}
              onActivate={handleActivate}
              onCompare={handleCompare}
              isComparing={!!compareSelection.find((c) => c.id === p.id)}
            />
          ))}
        </div>
      )}

      {showEditor && currentVariant && (
        <PromptEditor
          variant={currentVariant}
          currentContent={activePrompt?.content ?? ''}
          onSubmit={handleCreate}
          onCancel={() => setShowEditor(false)}
        />
      )}

      {showDiff && compareSelection.length === 2 && (
        <PromptDiff
          left={compareSelection[0]}
          right={compareSelection[1]}
          onClose={handleCloseDiff}
        />
      )}
    </div>
  );
}
