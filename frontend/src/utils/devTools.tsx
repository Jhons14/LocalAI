/**
 * Development tools and debugging utilities
 */

import React from 'react';
import { logger } from './logger';

// Performance monitoring
export class PerformanceMonitor {
  private static measurements: Map<string, number> = new Map();
  private static observers: PerformanceObserver[] = [];

  static startMeasurement(name: string): void {
    this.measurements.set(name, performance.now());
  }

  static endMeasurement(name: string): number | null {
    const startTime = this.measurements.get(name);
    if (!startTime) {
      logger.warn(`No start measurement found for: ${name}`, 'PERF');
      return null;
    }

    const duration = performance.now() - startTime;
    this.measurements.delete(name);

    logger.debug(`Performance: ${name} took ${duration.toFixed(2)}ms`, 'PERF');
    return duration;
  }

  static measureAsync<T>(name: string, fn: () => Promise<T>): Promise<T> {
    this.startMeasurement(name);
    return fn().finally(() => {
      this.endMeasurement(name);
    });
  }

  static measureSync<T>(name: string, fn: () => T): T {
    this.startMeasurement(name);
    try {
      return fn();
    } finally {
      this.endMeasurement(name);
    }
  }

  static observeResourceLoading(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'resource') {
          const resource = entry as PerformanceResourceTiming;
          logger.debug(`Resource loaded: ${resource.name}`, 'PERF', {
            duration: resource.duration,
            size: resource.transferSize,
            type: resource.initiatorType,
          });
        }
      }
    });

    observer.observe({ entryTypes: ['resource'] });
    this.observers.push(observer);
  }

  static observeNavigation(): void {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) {
      return;
    }

    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.entryType === 'navigation') {
          const nav = entry as PerformanceNavigationTiming;
          logger.info('Navigation timing', 'PERF', {
            domContentLoaded:
              nav.domContentLoadedEventEnd - nav.domContentLoadedEventStart,
            loadComplete: nav.loadEventEnd - nav.loadEventStart,
            totalTime: nav.loadEventEnd - nav.fetchStart,
          });
        }
      }
    });

    observer.observe({ entryTypes: ['navigation'] });
    this.observers.push(observer);
  }

  static disconnect(): void {
    this.observers.forEach((observer) => observer.disconnect());
    this.observers = [];
  }
}

// Memory usage monitoring
export class MemoryMonitor {
  static getMemoryInfo(): any {
    if (typeof window === 'undefined' || !('performance' in window)) {
      return null;
    }

    const memory = (performance as any).memory;
    if (!memory) return null;

    return {
      usedJSHeapSize: memory.usedJSHeapSize,
      totalJSHeapSize: memory.totalJSHeapSize,
      jsHeapSizeLimit: memory.jsHeapSizeLimit,
      usedPercent: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100,
    };
  }

  static logMemoryUsage(): void {
    const info = this.getMemoryInfo();
    if (info) {
      logger.debug(
        `Memory usage: ${(info.usedJSHeapSize / 1024 / 1024).toFixed(
          2
        )}MB (${info.usedPercent.toFixed(1)}%)`,
        'MEMORY',
        info
      );
    }
  }

  static startMonitoring(intervalMs = 30000): () => void {
    const interval = setInterval(() => {
      this.logMemoryUsage();
    }, intervalMs);

    return () => clearInterval(interval);
  }
}

// Component debugging
export function withDebugInfo<P extends object>(
  Component: React.ComponentType<P>,
  debugName?: string
): React.ComponentType<P> {
  const name =
    debugName || Component.displayName || Component.name || 'Unknown';

  const DebugWrapper = (props: P) => {
    const renderStart = performance.now();

    React.useEffect(() => {
      const renderTime = performance.now() - renderStart;
      logger.debug(
        `Component ${name} rendered in ${renderTime.toFixed(2)}ms`,
        'RENDER'
      );
    });

    React.useEffect(() => {
      logger.debug(`Component ${name} mounted`, 'LIFECYCLE');
      return () => {
        logger.debug(`Component ${name} unmounted`, 'LIFECYCLE');
      };
    }, []);

    return React.createElement(Component, props);
  };

  DebugWrapper.displayName = `withDebugInfo(${name})`;
  return DebugWrapper;
}

// Error boundary for development
export class DevErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    logger.error('DevErrorBoundary caught error', 'ERROR', {
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
    });
  }

  render() {
    if (this.state.hasError && import.meta.env.MODE === 'development') {
      return (
        <div
          style={{
            padding: '20px',
            border: '2px solid red',
            borderRadius: '8px',
            backgroundColor: '#ffe6e6',
            color: '#d00',
            fontFamily: 'monospace',
          }}
        >
          <h3>🚨 Development Error</h3>
          <p>
            <strong>Error:</strong> {this.state.error?.message}
          </p>
          <details>
            <summary>Stack Trace</summary>
            <pre style={{ overflow: 'auto', fontSize: '12px' }}>
              {this.state.error?.stack}
            </pre>
          </details>
          <button
            onClick={() => this.setState({ hasError: false, error: undefined })}
            style={{
              marginTop: '10px',
              padding: '5px 10px',
              backgroundColor: '#d00',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
          >
            Reset
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// Development utilities object
export const devTools = {
  // Log component props
  logProps: <P extends object>(component: string, props: P): void => {
    logger.debug(`${component} props:`, 'PROPS', props);
  },

  // Log state changes
  logStateChange: (component: string, oldState: any, newState: any): void => {
    logger.debug(`${component} state change:`, 'STATE', {
      old: oldState,
      new: newState,
    });
  },

  // Highlight element
  highlightElement: (element: HTMLElement, duration = 2000): void => {
    const originalOutline = element.style.outline;
    element.style.outline = '2px solid red';

    setTimeout(() => {
      element.style.outline = originalOutline;
    }, duration);
  },

  // Global error handler
  setupGlobalErrorHandling: (): void => {
    window.addEventListener('error', (event) => {
      logger.error('Global error:', 'ERROR', {
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        error: event.error,
      });
    });

    window.addEventListener('unhandledrejection', (event) => {
      logger.error('Unhandled promise rejection:', 'ERROR', {
        reason: event.reason,
      });
    });
  },

  // Performance marks
  mark: (name: string): void => {
    if (typeof performance !== 'undefined' && performance.mark) {
      performance.mark(name);
    }
  },

  measure: (name: string, startMark: string, endMark?: string): void => {
    if (typeof performance !== 'undefined' && performance.measure) {
      performance.measure(name, startMark, endMark);
    }
  },
};

// Initialize dev tools in development (browser only)
if (import.meta.env.MODE === 'development' && typeof window !== 'undefined') {
  // Make devTools available globally for debugging
  (window as any).__devTools = devTools;
  (window as any).__logger = logger;

  // Setup global error handling
  devTools.setupGlobalErrorHandling();

  // Start performance monitoring
  PerformanceMonitor.observeResourceLoading();
  PerformanceMonitor.observeNavigation();

  // Start memory monitoring
  const stopMemoryMonitoring = MemoryMonitor.startMonitoring();

  // Log initialization
  logger.info('Development tools initialized', 'DEV');
}
