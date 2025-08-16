/**
 * Centralized exports for all utilities
 */

// Common utilities
export {
  truncateText,
  capitalizeFirstLetter,
  slugify,
  formatDate,
  formatRelativeTime,
  groupBy,
  unique,
  chunk,
  omit,
  pick,
  deepClone,
  formatBytes,
  clamp,
  randomInt,
  sleep,
  retry,
  isValidUrl,
  getUrlDomain,
  safeLocalStorage,
  debounce,
  throttle,
  cn,
  isProduction,
  isDevelopment,
  copyToClipboard,
  downloadFile,
} from './common';

// Constants
export {
  API_CONFIG,
  STORAGE_CONFIG,
  UI_CONFIG,
  CHAT_CONFIG,
  VALIDATION_RULES,
  MODEL_PROVIDERS,
  POPULAR_MODELS,
  SUPPORTED_FILE_TYPES,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  THEME_CONFIG,
  A11Y_CONFIG,
  FEATURE_FLAGS,
  PERFORMANCE_CONFIG,
  SECURITY_CONFIG,
  DEV_CONFIG,
  REGEX_PATTERNS,
  STORAGE_KEYS,
  EVENT_NAMES,
  CSS_CLASSES,
} from './constants';

// Storage utilities
export {
  SecureStorage,
  ChatHistoryStorage,
  ModelStorage,
  ApiKeyStorage,
  PreferencesStorage,
  StorageMaintenance,
} from './storage';

// Validation utilities
export type { ValidationRule, ValidationResult } from './validation';
export { validateRequired, validateEmail, validateApiKey, validateMessage } from './validation';

// Logging utilities
export { logger, apiLogger, chatLogger, storageLogger, uiLogger, errorLogger } from './logger';

// Development tools
export { 
  PerformanceMonitor, 
  MemoryMonitor, 
  withDebugInfo, 
  DevErrorBoundary,
  devTools 
} from './devTools';

// Error monitoring
export type { ApplicationError, ErrorReporter } from './errorMonitoring';
export {
  errorMonitor,
  captureError,
  captureException,
  captureMessage,
  captureApiError,
  captureNetworkError,
  captureValidationError,
  captureStorageError,
  withErrorCapture,
  useErrorCapture,
} from './errorMonitoring';