/**
 * Latency distribution bar chart
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import type { LatencyBucket } from '../../types';

interface LatencyChartProps {
  data: LatencyBucket[];
}

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'];

export default function LatencyChart({ data }: LatencyChartProps) {
  if (data.every((d) => d.count === 0)) {
    return (
      <div className="analytics-chart-card">
        <h3>Latency Distribution</h3>
        <div className="analytics-empty">No latency data yet</div>
      </div>
    );
  }

  return (
    <div className="analytics-chart-card">
      <h3>Latency Distribution</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="bucket" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <YAxis tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '13px',
            }}
          />
          <Bar dataKey="count" name="Requests" radius={[4, 4, 0, 0]}>
            {data.map((_entry, index) => (
              <Cell key={index} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
