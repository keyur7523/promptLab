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
