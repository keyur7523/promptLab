/**
 * Settings page: API key management + data export
 */

import { useState, useEffect, useCallback } from 'react';
import type { ApiKeyInfo } from '../../types';
import { getKeyInfo, rotateKey, generateNewKey, getExportUrl } from '../../api/apiKeys';
import { setApiKey, getApiKey } from '../../api/config';
import ConfirmDialog from '../ConfirmDialog';

export default function Settings() {
  const [keyInfo, setKeyInfo] = useState<ApiKeyInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchKeyInfo = useCallback(async () => {
    try {
      const data = await getKeyInfo();
      setKeyInfo(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load key info');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchKeyInfo();
  }, [fetchKeyInfo]);

  const [showRotateConfirm, setShowRotateConfirm] = useState(false);

  const handleRotate = () => {
    setShowRotateConfirm(true);
  };

  const confirmRotate = async () => {
    setShowRotateConfirm(false);
    setActionLoading(true);
    setNewKey(null);
    try {
      const result = await rotateKey();
      setApiKey(result.api_key);
      setNewKey(result.api_key);
      await fetchKeyInfo();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to rotate key');
    } finally {
      setActionLoading(false);
    }
  };

  const handleGenerate = async () => {
    setActionLoading(true);
    setNewKey(null);
    try {
      const result = await generateNewKey();
      setNewKey(result.api_key);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate key');
    } finally {
      setActionLoading(false);
    }
  };

  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (newKey) {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExport = async (type: 'experiments' | 'conversations') => {
    const url = getExportUrl(type, type === 'conversations' ? 30 : undefined);
    try {
      const res = await fetch(url, { headers: { 'x-api-key': getApiKey() } });
      if (!res.ok) throw new Error(`Export failed: ${res.status}`);
      const blob = await res.blob();
      const blobUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = type === 'experiments' ? 'experiment_results.csv' : 'conversations_30d.csv';
      link.click();
      URL.revokeObjectURL(blobUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  const createdDate = keyInfo
    ? new Date(keyInfo.created_at).toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      })
    : '';

  return (
    <div className="experiments-container">
      <div className="experiments-header">
        <h1>Settings</h1>
      </div>

      {error && <div className="analytics-error">{error}</div>}

      {loading ? (
        <div className="analytics-loading">Loading...</div>
      ) : (
        <>
          {/* API Key Management */}
          <div className="settings-section">
            <h2>API Key</h2>

            {keyInfo && (
              <div className="settings-card">
                <div className="settings-grid">
                  <div className="settings-label">Key Hash</div>
                  <div className="settings-value">
                    <code>{keyInfo.key_prefix}</code>
                  </div>
                  <div className="settings-label">Created</div>
                  <div className="settings-value">{createdDate}</div>
                  <div className="settings-label">Rate Limit</div>
                  <div className="settings-value">{keyInfo.rate_limit} req/hour</div>
                  <div className="settings-label">Usage</div>
                  <div className="settings-value">
                    {keyInfo.conversations} conversations, {keyInfo.messages} messages
                  </div>
                </div>

                <div className="settings-actions">
                  <button
                    className="btn-primary"
                    onClick={handleRotate}
                    disabled={actionLoading}
                  >
                    Rotate Key
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={handleGenerate}
                    disabled={actionLoading}
                  >
                    Generate New Key
                  </button>
                </div>
              </div>
            )}

            {newKey && (
              <div className="new-key-banner">
                <div className="new-key-banner__label">New API Key (save it now!):</div>
                <div className="new-key-banner__key">
                  <code>{newKey}</code>
                  <button className="btn-text" onClick={handleCopy}>{copied ? 'Copied!' : 'Copy'}</button>
                </div>
              </div>
            )}
          </div>

          {/* Data Export */}
          <div className="settings-section">
            <h2>Data Export</h2>
            <div className="settings-card">
              <p className="settings-desc">Download your data as CSV files for analysis in spreadsheets or BI tools.</p>
              <div className="settings-actions">
                <button className="btn-secondary" onClick={() => handleExport('experiments')}>
                  Export Experiment Results
                </button>
                <button className="btn-secondary" onClick={() => handleExport('conversations')}>
                  Export Conversations (30d)
                </button>
              </div>
            </div>
          </div>
        </>
      )}

      {showRotateConfirm && (
        <ConfirmDialog
          message="Rotate your API key? The current key will stop working immediately."
          onConfirm={confirmRotate}
          onCancel={() => setShowRotateConfirm(false)}
        />
      )}
    </div>
  );
}
