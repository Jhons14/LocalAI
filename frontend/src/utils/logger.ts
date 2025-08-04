/**
 * Comprehensive logging utility with different levels and contexts
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

export interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: number;
  context?: string;
  data?: any;
  stack?: string;
}

export interface LoggerConfig {
  level: LogLevel;
  enableConsole: boolean;
  enableStorage: boolean;
  maxStorageEntries: number;
  contexts: string[];
}

class Logger {
  private config: LoggerConfig = {
    level: 'info',
    enableConsole: true,
    enableStorage: false,
    maxStorageEntries: 1000,
    contexts: [],
  };

  private logs: LogEntry[] = [];
  private readonly levels: Record<LogLevel, number> = {
    debug: 0,
    info: 1,
    warn: 2,
    error: 3,
  };

  configure(config: Partial<LoggerConfig>): void {
    this.config = { ...this.config, ...config };
  }

  private shouldLog(level: LogLevel, context?: string): boolean {
    const levelCheck = this.levels[level] >= this.levels[this.config.level];
    const contextCheck = !context || 
      this.config.contexts.length === 0 || 
      this.config.contexts.includes(context);
    
    return levelCheck && contextCheck;
  }

  private createLogEntry(
    level: LogLevel,
    message: string,
    context?: string,
    data?: any
  ): LogEntry {
    return {
      level,
      message,
      timestamp: Date.now(),
      context,
      data,
      stack: level === 'error' ? new Error().stack : undefined,
    };
  }

  private writeLog(entry: LogEntry): void {
    if (this.config.enableConsole) {
      const prefix = `[${entry.level.toUpperCase()}]${entry.context ? ` [${entry.context}]` : ''}`;
      const timestamp = new Date(entry.timestamp).toISOString();
      
      switch (entry.level) {
        case 'debug':
          console.debug(`${prefix} ${timestamp}:`, entry.message, entry.data);
          break;
        case 'info':
          console.info(`${prefix} ${timestamp}:`, entry.message, entry.data);
          break;
        case 'warn':
          console.warn(`${prefix} ${timestamp}:`, entry.message, entry.data);
          break;
        case 'error':
          console.error(`${prefix} ${timestamp}:`, entry.message, entry.data);
          if (entry.stack) {
            console.error('Stack trace:', entry.stack);
          }
          break;
      }
    }

    if (this.config.enableStorage) {
      this.logs.push(entry);
      if (this.logs.length > this.config.maxStorageEntries) {
        this.logs.shift();
      }
    }
  }

  debug(message: string, context?: string, data?: any): void {
    if (this.shouldLog('debug', context)) {
      this.writeLog(this.createLogEntry('debug', message, context, data));
    }
  }

  info(message: string, context?: string, data?: any): void {
    if (this.shouldLog('info', context)) {
      this.writeLog(this.createLogEntry('info', message, context, data));
    }
  }

  warn(message: string, context?: string, data?: any): void {
    if (this.shouldLog('warn', context)) {
      this.writeLog(this.createLogEntry('warn', message, context, data));
    }
  }

  error(message: string, context?: string, error?: Error | any): void {
    if (this.shouldLog('error', context)) {
      const entry = this.createLogEntry('error', message, context, error);
      if (error instanceof Error) {
        entry.stack = error.stack;
      }
      this.writeLog(entry);
    }
  }

  getLogs(level?: LogLevel, context?: string): LogEntry[] {
    return this.logs.filter(log => 
      (!level || log.level === level) &&
      (!context || log.context === context)
    );
  }

  clearLogs(): void {
    this.logs = [];
  }

  exportLogs(): string {
    return JSON.stringify(this.logs, null, 2);
  }

  createChildLogger(context: string): Logger {
    const child = new Logger();
    child.configure(this.config);
    
    return {
      debug: (message: string, data?: any) => this.debug(message, context, data),
      info: (message: string, data?: any) => this.info(message, context, data),
      warn: (message: string, data?: any) => this.warn(message, context, data),
      error: (message: string, error?: any) => this.error(message, context, error),
      getLogs: () => this.getLogs(undefined, context),
      clearLogs: () => {},
      exportLogs: () => JSON.stringify(this.getLogs(undefined, context), null, 2),
      createChildLogger: (subContext: string) => this.createChildLogger(`${context}:${subContext}`),
      configure: () => {},
    } as Logger;
  }
}

// Global logger instance
export const logger = new Logger();

// Configure based on environment
if (typeof window !== 'undefined') {
  const isDev = import.meta.env.MODE === 'development';
  logger.configure({
    level: isDev ? 'debug' : 'warn',
    enableConsole: true,
    enableStorage: isDev,
  });
}

// Export specific loggers for different parts of the app
export const apiLogger = logger.createChildLogger('API');
export const chatLogger = logger.createChildLogger('CHAT');
export const storageLogger = logger.createChildLogger('STORAGE');
export const uiLogger = logger.createChildLogger('UI');
export const errorLogger = logger.createChildLogger('ERROR');