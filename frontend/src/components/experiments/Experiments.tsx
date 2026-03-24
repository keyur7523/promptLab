/**
 * Experiment management page
 */

import { useState, useEffect, useCallback } from 'react';
import type { Experiment } from '../../types';
import {
  listExperiments,
  createExperiment,
  updateExperiment,
  deleteExperiment,
} from '../../api/experiments';
import ExperimentCard from './ExperimentCard';
import ExperimentForm from './ExperimentForm';
import ConfirmDialog from '../ConfirmDialog';

export default function Experiments() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingExperiment, setEditingExperiment] = useState<Experiment | undefined>();

  const fetchExperiments = useCallback(async () => {
    try {
      const data = await listExperiments();
      setExperiments(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load experiments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchExperiments();
  }, [fetchExperiments]);

  const handleCreate = async (data: { key: string; description: string; variants: Record<string, number> }) => {
    try {
      await createExperiment(data);
      setShowForm(false);
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create experiment');
    }
  };

  const handleEdit = (experiment: Experiment) => {
    setEditingExperiment(experiment);
    setShowForm(true);
  };

  const handleUpdate = async (data: { key: string; description: string; variants: Record<string, number> }) => {
    if (!editingExperiment) return;
    try {
      await updateExperiment(editingExperiment.id, {
        description: data.description,
        variants: data.variants,
      });
      setShowForm(false);
      setEditingExperiment(undefined);
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update experiment');
    }
  };

  const handleToggleActive = async (id: string, active: boolean) => {
    try {
      await updateExperiment(id, { active });
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update experiment');
    }
  };

  const [deleteTarget, setDeleteTarget] = useState<string | null>(null);

  const handleDelete = (id: string) => {
    setDeleteTarget(id);
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      await deleteExperiment(deleteTarget);
      await fetchExperiments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete experiment');
    } finally {
      setDeleteTarget(null);
    }
  };

  const handleCloseForm = () => {
    setShowForm(false);
    setEditingExperiment(undefined);
  };

  const activeCount = experiments.filter((e) => e.active).length;

  return (
    <div className="experiments-container">
      <div className="experiments-header">
        <div>
          <h1>Experiments</h1>
          <p className="experiments-subtitle">
            {experiments.length} experiment{experiments.length !== 1 ? 's' : ''} &middot; {activeCount} active
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => {
            setEditingExperiment(undefined);
            setShowForm(true);
          }}
        >
          + New Experiment
        </button>
      </div>

      {error && <div className="analytics-error">{error}</div>}

      {loading ? (
        <div className="analytics-loading">Loading experiments...</div>
      ) : experiments.length === 0 ? (
        <div className="experiments-empty">
          <p>No experiments yet. Create one to start A/B testing your prompts.</p>
        </div>
      ) : (
        <div className="experiments-list">
          {experiments.map((exp) => (
            <ExperimentCard
              key={exp.id}
              experiment={exp}
              onToggleActive={handleToggleActive}
              onEdit={handleEdit}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {showForm && (
        <ExperimentForm
          experiment={editingExperiment}
          onSubmit={editingExperiment ? handleUpdate : handleCreate}
          onCancel={handleCloseForm}
        />
      )}

      {deleteTarget && (
        <ConfirmDialog
          message="Delete this experiment? This cannot be undone."
          onConfirm={confirmDelete}
          onCancel={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
