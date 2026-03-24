/**
 * Type definitions for AI Chat Platform
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  variant?: string;
  model?: string;
  timestamp?: Date;
  tokens_in?: number;
  tokens_out?: number;
  latency_ms?: number;
  cost?: number;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface FeedbackRequest {
  message_id: string;
  rating: 1 | -1;
  comment?: string;
}

export interface StreamMetadata {
  done: boolean;
  message_id: string;
  conversation_id: string;
  variant: string;
  model: string;
  tokens_in?: number;
  tokens_out?: number;
  latency_ms?: number;
  cost?: number;
}

// Analytics types

export interface AnalyticsOverview {
  days: number;
  total_conversations: number;
  total_messages: number;
  total_cost: number;
  avg_cost_per_message: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_tokens_in: number;
  total_tokens_out: number;
  total_feedback: number;
  approval_rate: number;
}

export interface UsageDataPoint {
  date: string;
  messages: number;
  cost: number;
  avg_latency_ms: number;
  tokens_total: number;
}

export interface ExperimentStats {
  variant: string;
  messages: number;
  avg_latency_ms: number;
  avg_cost: number;
  approval_rate: number;
  sample_size: number;
}

export interface LatencyBucket {
  bucket: string;
  count: number;
}

// Experiment management types

export interface Experiment {
  id: string;
  key: string;
  description: string;
  variants: Record<string, number>;
  active: boolean;
  created_at: string;
}

export interface ExperimentCreateRequest {
  key: string;
  description: string;
  variants: Record<string, number>;
}

export interface ExperimentUpdateRequest {
  description?: string;
  variants?: Record<string, number>;
  active?: boolean;
}

// Conversation history types

export interface ConversationSummary {
  id: string;
  created_at: string;
  message_count: number;
  preview: string;
}

export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  variant?: string;
  model?: string;
  tokens_in?: number;
  tokens_out?: number;
  latency_ms?: number;
  cost?: number;
  created_at: string;
}

// Prompt version types

export interface PromptVersion {
  id: string;
  variant: string;
  version: number;
  content: string;
  is_active: boolean;
  created_at: string;
}

// API key types

export interface ApiKeyInfo {
  user_id: string;
  rate_limit: number;
  created_at: string;
  conversations: number;
  messages: number;
  key_prefix: string;
}
