/**
 * Overview stat cards grid
 */

import type { AnalyticsOverview } from '../../types';

interface OverviewCardsProps {
  data: AnalyticsOverview;
}

function formatCost(cost: number): string {
  if (cost === 0) return '$0.00';
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function formatLatency(ms: number): string {
  if (ms === 0) return '0ms';
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

export default function OverviewCards({ data }: OverviewCardsProps) {
  const cards = [
    {
      label: 'Messages',
      value: data.total_messages.toLocaleString(),
      sub: `${data.total_conversations} conversations`,
      accent: 'blue',
    },
    {
      label: 'Total Cost',
      value: formatCost(data.total_cost),
      sub: `${formatCost(data.avg_cost_per_message)} avg/msg`,
      accent: 'green',
    },
    {
      label: 'Avg Latency',
      value: formatLatency(data.avg_latency_ms),
      sub: `P95: ${formatLatency(data.p95_latency_ms)}`,
      accent: 'yellow',
    },
    {
      label: 'Approval Rate',
      value: `${data.approval_rate}%`,
      sub: `${data.total_feedback} ratings`,
      accent: 'purple',
    },
    {
      label: 'Tokens In',
      value: data.total_tokens_in.toLocaleString(),
      sub: 'input tokens',
      accent: 'blue',
    },
    {
      label: 'Tokens Out',
      value: data.total_tokens_out.toLocaleString(),
      sub: 'output tokens',
      accent: 'blue',
    },
  ];

  return (
    <div className="overview-cards">
      {cards.map((card) => (
        <div key={card.label} className={`overview-card overview-card--${card.accent}`}>
          <div className="overview-card__label">{card.label}</div>
          <div className="overview-card__value">{card.value}</div>
          <div className="overview-card__sub">{card.sub}</div>
        </div>
      ))}
    </div>
  );
}
