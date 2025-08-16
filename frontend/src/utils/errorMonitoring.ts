/**
 * Comprehensive error monitoring and reporting system
 */

import { logger, errorLogger } from './logger';

// Error types
export interface ApplicationError {
  id: string;
  type: 'network' | 'validation' | 'runtime' | 'api' | 'storage' | 'unknown';
  message: string;
  stack?: string;
  context?: string;
  metadata?: Record<string, any>;
  timestamp: number;
  url?: string;
  userAgent?: string;
  userId?: string;
  sessionId?: string;
}

// Error reporter interface
export interface ErrorReporter {
  report(error: ApplicationError): Promise<void>;
}

// Console error reporter (for development)
class ConsoleErrorReporter implements ErrorReporter {
  async report(error: ApplicationError): Promise<void> {
    errorLogger.error(
      `${error.type.toUpperCase()}: ${error.message}`,
      error.context,
      {
        id: error.id,
        stack: error.stack,
        metadata: error.metadata,
        url: error.url,
        userAgent: error.userAgent,
      }
    );
  }
}

// Storage error reporter (stores errors locally)
class StorageErrorReporter implements ErrorReporter {
  private readonly storageKey = 'localai_error_logs';
  private readonly maxErrors = 100;

  async report(error: ApplicationError): Promise<void> {
    try {
      const existingErrors = this.getStoredErrors();
      const updatedErrors = [error, ...existingErrors].slice(0, this.maxErrors);
      
      localStorage.setItem(this.storageKey, JSON.stringify(updatedErrors));
    } catch (storageError) {
      console.error('Failed to store error:', storageError);
    }
  }

  getStoredErrors(): ApplicationError[] {
    try {
      const stored = localStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  }

  clearStoredErrors(): void {
    localStorage.removeItem(this.storageKey);
  }

  exportErrors(): string {
    return JSON.stringify(this.getStoredErrors(), null, 2);
  }
}

// Remote error reporter (for production monitoring)
class RemoteErrorReporter implements ErrorReporter {
  constructor(private endpoint: string) {}

  async report(error: ApplicationError): Promise<void> {
    try {
      await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(error),
      });
    } catch (networkError) {
      console.error('Failed to send error to remote service:', networkError);
    }
  }
}

// Main error monitoring class
class ErrorMonitor {
  private reporters: ErrorReporter[] = [];
  private sessionId: string = this.generateSessionId();
  private errorCount = 0;

  constructor() {
    this.setupGlobalHandlers();
    
    // Add default reporters
    this.addReporter(new ConsoleErrorReporter());
    
    if (import.meta.env.MODE === 'development') {
      this.addReporter(new StorageErrorReporter());
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private setupGlobalHandlers(): void {
    if (typeof window === 'undefined') return;

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      this.captureError({
        type: 'runtime',
        message: event.message,
        stack: event.error?.stack,
        context: 'global',
        metadata: {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        },
      });
    });

    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.captureError({
        type: 'runtime',
        message: event.reason?.message || 'Unhandled promise rejection',
        stack: event.reason?.stack,
        context: 'promise',
        metadata: {
          reason: event.reason,
        },
      });
    });

    // Handle resource loading errors
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.captureError({
          type: 'network',
          message: `Failed to load resource: ${(event.target as any)?.src || (event.target as any)?.href}`,
          context: 'resource',
          metadata: {
            element: event.target?.tagName,
            src: (event.target as any)?.src,
            href: (event.target as any)?.href,
          },
        });
      }
    }, true);
  }

  addReporter(reporter: ErrorReporter): void {
    this.reporters.push(reporter);
  }

  removeReporter(reporter: ErrorReporter): void {
    const index = this.reporters.indexOf(reporter);
    if (index > -1) {
      this.reporters.splice(index, 1);
    }
  }

  captureError(errorData: Partial<ApplicationError>): string {
    this.errorCount++;
    
    const error: ApplicationError = {
      id: `error_${Date.now()}_${this.errorCount}`,
      type: errorData.type || 'unknown',
      message: errorData.message || 'Unknown error',
      stack: errorData.stack,
      context: errorData.context,
      metadata: errorData.metadata,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      sessionId: this.sessionId,
      ...errorData,
    };

    // Report to all configured reporters
    this.reporters.forEach(reporter => {
      reporter.report(error).catch(reportError => {
        console.error('Error reporter failed:', reportError);
      });
    });

    return error.id;
  }

  captureException(error: Error, context?: string, metadata?: Record<string, any>): string {
    return this.captureError({
      type: 'runtime',
      message: error.message,
      stack: error.stack,
      context,
      metadata,
    });
  }

  captureMessage(message: string, context?: string, metadata?: Record<string, any>): string {
    return this.captureError({
      type: 'unknown',
      message,
      context,
      metadata,
    });
  }

  // API error handling
  captureApiError(
    endpoint: string, 
    status: number, 
    statusText: string, 
    response?: any
  ): string {
    return this.captureError({
      type: 'api',
      message: `API Error: ${status} ${statusText}`,
      context: 'api',
      metadata: {
        endpoint,
        status,
        statusText,
        response,
      },
    });
  }

  // Network error handling
  captureNetworkError(url: string, error: Error): string {
    return this.captureError({
      type: 'network',
      message: `Network Error: ${error.message}`,
      stack: error.stack,
      context: 'network',
      metadata: {
        url,
        name: error.name,
      },
    });
  }

  // Validation error handling
  captureValidationError(field: string, value: any, rule: string): string {
    return this.captureError({
      type: 'validation',
      message: `Validation failed for field '${field}' with rule '${rule}'`,
      context: 'validation',
      metadata: {
        field,
        value,
        rule,
      },
    });
  }

  // Storage error handling
  captureStorageError(operation: string, key: string, error: Error): string {
    return this.captureError({
      type: 'storage',
      message: `Storage Error: ${operation} failed for key '${key}'`,
      stack: error.stack,
      context: 'storage',
      metadata: {
        operation,
        key,
        name: error.name,
      },
    });
  }

  getSessionId(): string {
    return this.sessionId;
  }

  getErrorCount(): number {
    return this.errorCount;
  }
}

// Global error monitor instance
export const errorMonitor = new ErrorMonitor();

// Convenience functions
export const captureError = (error: Partial<ApplicationError>): string => 
  errorMonitor.captureError(error);

export const captureException = (error: Error, context?: string, metadata?: Record<string, any>): string =>
  errorMonitor.captureException(error, context, metadata);

export const captureMessage = (message: string, context?: string, metadata?: Record<string, any>): string =>
  errorMonitor.captureMessage(message, context, metadata);

export const captureApiError = (endpoint: string, status: number, statusText: string, response?: any): string =>
  errorMonitor.captureApiError(endpoint, status, statusText, response);

export const captureNetworkError = (url: string, error: Error): string =>
  errorMonitor.captureNetworkError(url, error);

export const captureValidationError = (field: string, value: any, rule: string): string =>
  errorMonitor.captureValidationError(field, value, rule);

export const captureStorageError = (operation: string, key: string, error: Error): string =>
  errorMonitor.captureStorageError(operation, key, error);

// Error boundary helper
export const withErrorCapture = <T extends (...args: any[]) => any>(
  fn: T,
  context?: string
): T => {
  return ((...args: any[]) => {
    try {
      const result = fn(...args);
      
      // Handle async functions
      if (result instanceof Promise) {
        return result.catch((error: Error) => {
          captureException(error, context);
          throw error;
        });
      }
      
      return result;
    } catch (error) {
      captureException(error as Error, context);
      throw error;
    }
  }) as T;
};

// React hook for error capture
export const useErrorCapture = () => {
  return {
    captureError,
    captureException,
    captureMessage,
    captureApiError,
    captureNetworkError,
    captureValidationError,
    captureStorageError,
  };
};