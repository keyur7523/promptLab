/**
 * Experiment variant comparison table
 */

import type { ExperimentStats } from '../../types';

interface ExperimentTableProps {
  data: ExperimentStats[];
}

export default function ExperimentTable({ data }: ExperimentTableProps) {
  if (data.length === 0) {
    return (
      <div className="analytics-chart-card">
        <h3>Experiment Performance</h3>
        <div className="analytics-empty">No experiment data yet</div>
      </div>
    );
  }

  return (
    <div className="analytics-chart-card">
      <h3>Experiment Performance</h3>
      <div className="experiment-table-wrapper">
        <table className="experiment-table">
          <thead>
            <tr>
              <th>Variant</th>
              <th>Messages</th>
              <th>Avg Latency</th>
              <th>Avg Cost</th>
              <th>Approval</th>
              <th>Sample Size</th>
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.variant}>
                <td>
                  <span className="variant-badge">{row.variant}</span>
                </td>
                <td>{row.messages.toLocaleString()}</td>
                <td>{row.avg_latency_ms < 1000 ? `${row.avg_latency_ms}ms` : `${(row.avg_latency_ms / 1000).toFixed(1)}s`}</td>
                <td>${row.avg_cost.toFixed(4)}</td>
                <td>
                  <span className={`approval-badge ${row.approval_rate >= 70 ? 'good' : row.approval_rate >= 40 ? 'neutral' : 'poor'}`}>
                    {row.approval_rate}%
                  </span>
                </td>
                <td>{row.sample_size}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
