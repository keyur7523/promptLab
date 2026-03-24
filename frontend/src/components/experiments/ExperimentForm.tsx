/**
 * Form for creating or editing an experiment
 */

import { useState } from 'react';
import type { Experiment } from '../../types';

interface VariantRow {
  name: string;
  weight: number;
}

interface ExperimentFormProps {
  experiment?: Experiment;
  onSubmit: (data: { key: string; description: string; variants: Record<string, number> }) => void;
  onCancel: () => void;
}

export default function ExperimentForm({ experiment, onSubmit, onCancel }: ExperimentFormProps) {
  const isEditing = !!experiment;

  const [key, setKey] = useState(experiment?.key ?? '');
  const [description, setDescription] = useState(experiment?.description ?? '');
  const [variants, setVariants] = useState<VariantRow[]>(() => {
    if (experiment) {
      return Object.entries(experiment.variants)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([name, weight]) => ({ name, weight }));
    }
    return [
      { name: 'control', weight: 50 },
      { name: 'variant_a', weight: 50 },
    ];
  });
  const [error, setError] = useState<string | null>(null);

  const totalWeight = variants.reduce((sum, v) => sum + v.weight, 0);

  const addVariant = () => {
    setVariants([...variants, { name: '', weight: 0 }]);
  };

  const removeVariant = (index: number) => {
    if (variants.length <= 1) return;
    setVariants(variants.filter((_, i) => i !== index));
  };

  const updateVariant = (index: number, field: 'name' | 'weight', value: string | number) => {
    setVariants(variants.map((v, i) => (i === index ? { ...v, [field]: value } : v)));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!key.trim()) {
      setError('Key is required');
      return;
    }

    if (variants.some((v) => !v.name.trim())) {
      setError('All variant names are required');
      return;
    }

    const names = variants.map((v) => v.name.trim());
    if (new Set(names).size !== names.length) {
      setError('Variant names must be unique');
      return;
    }

    if (totalWeight !== 100) {
      setError(`Weights must sum to 100 (currently ${totalWeight})`);
      return;
    }

    const variantMap: Record<string, number> = {};
    for (const v of variants) {
      variantMap[v.name.trim()] = v.weight;
    }

    onSubmit({ key: key.trim(), description: description.trim(), variants: variantMap });
  };

  return (
    <div className="experiment-form-overlay" onClick={onCancel}>
      <div className="experiment-form" onClick={(e) => e.stopPropagation()}>
        <h2>{isEditing ? 'Edit Experiment' : 'Create Experiment'}</h2>

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label>Key</label>
            <input
              type="text"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              placeholder="e.g. prompt_experiment_v2"
              disabled={isEditing}
              maxLength={100}
            />
          </div>

          <div className="form-field">
            <label>Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What this experiment tests"
              maxLength={500}
            />
          </div>

          <div className="form-field">
            <label>
              Variants
              <span className={`weight-total ${totalWeight === 100 ? 'valid' : 'invalid'}`}>
                {totalWeight}/100
              </span>
            </label>
            <div className="variant-rows">
              {variants.map((v, i) => (
                <div key={i} className="variant-row">
                  <input
                    type="text"
                    value={v.name}
                    onChange={(e) => updateVariant(i, 'name', e.target.value)}
                    placeholder="Variant name"
                    className="variant-name-input"
                  />
                  <input
                    type="number"
                    value={v.weight}
                    onChange={(e) => updateVariant(i, 'weight', parseInt(e.target.value) || 0)}
                    min={0}
                    max={100}
                    className="variant-weight-input"
                  />
                  <span className="variant-percent">%</span>
                  <button
                    type="button"
                    className="variant-remove-btn"
                    onClick={() => removeVariant(i)}
                    disabled={variants.length <= 1}
                    title="Remove variant"
                  >
                    x
                  </button>
                </div>
              ))}
            </div>
            <button type="button" className="btn-text" onClick={addVariant}>
              + Add variant
            </button>
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="form-actions">
            <button type="button" className="btn-secondary" onClick={onCancel}>
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={totalWeight !== 100}>
              {isEditing ? 'Save Changes' : 'Create Experiment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
