/**
 * Card displaying a single experiment with controls
 */

import type { Experiment } from '../../types';

interface ExperimentCardProps {
  experiment: Experiment;
  onToggleActive: (id: string, active: boolean) => void;
  onEdit: (experiment: Experiment) => void;
  onDelete: (id: string) => void;
}

export default function ExperimentCard({ experiment, onToggleActive, onEdit, onDelete }: ExperimentCardProps) {
  const totalWeight = Object.values(experiment.variants).reduce((a, b) => a + b, 0);
  const createdDate = new Date(experiment.created_at).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className={`experiment-card ${experiment.active ? '' : 'experiment-card--inactive'}`}>
      <div className="experiment-card__header">
        <div>
          <div className="experiment-card__key">{experiment.key}</div>
          <div className="experiment-card__desc">{experiment.description || 'No description'}</div>
        </div>
        <div className="experiment-card__actions">
          <label className="toggle-switch" title={experiment.active ? 'Active' : 'Inactive'}>
            <input
              type="checkbox"
              checked={experiment.active}
              onChange={() => onToggleActive(experiment.id, !experiment.active)}
            />
            <span className="toggle-slider" />
          </label>
        </div>
      </div>

      <div className="experiment-card__variants">
        <div className="variant-bar">
          {Object.entries(experiment.variants)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([name, weight]) => (
              <div
                key={name}
                className="variant-bar__segment"
                style={{ width: `${(weight / totalWeight) * 100}%` }}
                title={`${name}: ${weight}%`}
              >
                <span className="variant-bar__label">{name}</span>
                <span className="variant-bar__weight">{weight}%</span>
              </div>
            ))}
        </div>
      </div>

      <div className="experiment-card__footer">
        <span className="experiment-card__date">Created {createdDate}</span>
        <div className="experiment-card__footer-actions">
          <button className="btn-text" onClick={() => onEdit(experiment)}>Edit</button>
          <button className="btn-text btn-text--danger" onClick={() => onDelete(experiment.id)}>Delete</button>
        </div>
      </div>
    </div>
  );
}
