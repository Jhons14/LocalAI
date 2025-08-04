/**
 * Event and state management types
 */

// Custom event types
export interface CustomEvent<T = any> {
  type: string;
  payload: T;
  timestamp: number;
  source?: string;
}

// Event handler types
export type EventHandler<T = any> = (event: CustomEvent<T>) => void;

// Event emitter interface
export interface EventEmitter {
  on<T>(eventType: string, handler: EventHandler<T>): () => void;
  off<T>(eventType: string, handler: EventHandler<T>): void;
  emit<T>(eventType: string, payload: T): void;
  once<T>(eventType: string, handler: EventHandler<T>): void;
  clear(): void;
}

// Application events
export type AppEvent = 
  | 'app:init'
  | 'app:ready'
  | 'app:error'
  | 'auth:login'
  | 'auth:logout'
  | 'chat:message:sent'
  | 'chat:message:received'
  | 'model:connected'
  | 'model:disconnected'
  | 'storage:updated'
  | 'theme:changed'
  | 'error:occurred';

// State change events
export interface StateChangeEvent<T = any> {
  type: 'state:change';
  path: string;
  oldValue: T;
  newValue: T;
  timestamp: number;
}

// Error events
export interface ErrorEvent {
  type: 'error';
  error: Error;
  context?: string;
  timestamp: number;
  stack?: string;
  userAgent?: string;
  url?: string;
}

// Performance events
export interface PerformanceEvent {
  type: 'performance';
  metric: string;
  value: number;
  timestamp: number;
  tags?: Record<string, string>;
}

// User interaction events
export interface UserInteractionEvent {
  type: 'interaction';
  action: string;
  element?: string;
  timestamp: number;
  metadata?: Record<string, any>;
}

// Async operation events
export interface AsyncOperationEvent {
  type: 'async:start' | 'async:success' | 'async:error';
  operationId: string;
  operation: string;
  timestamp: number;
  duration?: number;
  error?: Error;
  result?: any;
}

// Event subscription options
export interface SubscriptionOptions {
  once?: boolean;
  priority?: number;
  filter?: (event: CustomEvent) => boolean;
}

// Event bus interface
export interface EventBus {
  subscribe<T>(
    eventType: string, 
    handler: EventHandler<T>, 
    options?: SubscriptionOptions
  ): () => void;
  unsubscribe<T>(eventType: string, handler: EventHandler<T>): void;
  publish<T>(eventType: string, payload: T): void;
  clear(): void;
  getSubscribers(eventType: string): number;
}