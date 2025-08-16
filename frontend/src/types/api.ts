/**
 * API related types and interfaces
 */

// HTTP Method types
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

// API Response wrapper
export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  message?: string;
  error?: string;
  timestamp: number;
}

// API Error types
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}

// Request configuration
export interface RequestConfig {
  method: HttpMethod;
  headers?: Record<string, string>;
  body?: any;
  timeout?: number;
  retries?: number;
  abortSignal?: AbortSignal;
}

// Streaming response
export interface StreamResponse {
  chunk: string;
  done: boolean;
  error?: string;
}

// API endpoints
export interface ApiEndpoints {
  chat: '/chat';
  models: '/models';
  configure: '/configure';
  keys: '/keys';
  health: '/health';
}

// Model configuration
export interface ModelConfig {
  model: string;
  provider: string;
  apiKey?: string;
  temperature?: number;
  maxTokens?: number;
  topP?: number;
  frequencyPenalty?: number;
  presencePenalty?: number;
}

// Chat request/response types
export interface ChatRequest {
  message: string;
  threadId: string;
  model: string;
  provider: string;
  config?: Partial<ModelConfig>;
}

export interface ChatResponse {
  id: string;
  content: string;
  role: 'assistant';
  timestamp: number;
  model: string;
  tokenUsage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

// Model listing
export interface AvailableModel {
  id: string;
  name: string;
  provider: string;
  description?: string;
  contextLength?: number;
  pricing?: {
    input: number;
    output: number;
  };
}

export interface ModelsResponse {
  models: AvailableModel[];
  providers: string[];
}