/**
 * Daily usage time-series chart
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import type { UsageDataPoint } from '../../types';

interface UsageChartProps {
  data: UsageDataPoint[];
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function UsageChart({ data }: UsageChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    dateLabel: formatDate(d.date),
  }));

  if (formatted.length === 0) {
    return (
      <div className="analytics-chart-card">
        <h3>Daily Usage</h3>
        <div className="analytics-empty">No usage data yet</div>
      </div>
    );
  }

  return (
    <div className="analytics-chart-card">
      <h3>Daily Usage</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={formatted} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="dateLabel" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <YAxis yAxisId="left" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12 }} stroke="#9ca3af" />
          <Tooltip
            contentStyle={{
              backgroundColor: '#fff',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '13px',
            }}
          />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="messages"
            stroke="#3b82f6"
            fill="#dbeafe"
            name="Messages"
          />
          <Area
            yAxisId="right"
            type="monotone"
            dataKey="avg_latency_ms"
            stroke="#f59e0b"
            fill="#fef3c7"
            name="Avg Latency (ms)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
