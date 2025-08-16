/**
 * Application constants and configuration
 */

// API Configuration
export const API_CONFIG = {
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

// Storage Configuration
export const STORAGE_CONFIG = {
  MAX_CHAT_HISTORY_DAYS: 30,
  MAX_MESSAGES_PER_THREAD: 1000,
  MAX_THREADS: 50,
  AUTO_SAVE_DELAY: 1000, // 1 second debounce
  CLEANUP_INTERVAL: 24 * 60 * 60 * 1000, // 24 hours
} as const;

// UI Configuration
export const UI_CONFIG = {
  TOAST_DURATION: 5000, // 5 seconds
  ANIMATION_DURATION: 300, // 300ms
  MOBILE_BREAKPOINT: 768, // px
  TABLET_BREAKPOINT: 1024, // px
  MAX_MOBILE_WIDTH: '767px',
  MAX_TABLET_WIDTH: '1023px',
} as const;

// Chat Configuration
export const CHAT_CONFIG = {
  MAX_MESSAGE_LENGTH: 4000,
  STREAMING_CHUNK_SIZE: 1024,
  TYPING_INDICATOR_DELAY: 500,
  MESSAGE_RETRY_ATTEMPTS: 3,
} as const;

// Validation Rules
export const VALIDATION_RULES = {
  API_KEY: {
    MIN_LENGTH: 20,
    MAX_LENGTH: 200,
    PATTERN: /^[a-zA-Z0-9._-]+$/,
  },
  MESSAGE: {
    MAX_LENGTH: CHAT_CONFIG.MAX_MESSAGE_LENGTH,
    MIN_LENGTH: 1,
  },
  MODEL_NAME: {
    MIN_LENGTH: 1,
    MAX_LENGTH: 100,
    PATTERN: /^[a-zA-Z0-9._-]+$/,
  },
} as const;

// Model Providers
export const MODEL_PROVIDERS = {
  OPENAI: 'openai',
  OLLAMA: 'ollama',
  ANTHROPIC: 'anthropic',
  HUGGINGFACE: 'huggingface',
} as const;

// Popular Models
export const POPULAR_MODELS = {
  [MODEL_PROVIDERS.OPENAI]: [
    'gpt-4',
    'gpt-3.5-turbo',
    'gpt-4-turbo',
    'gpt-4o',
  ],
  [MODEL_PROVIDERS.OLLAMA]: [
    'llama2',
    'codellama',
    'mistral',
    'neural-chat',
  ],
  [MODEL_PROVIDERS.ANTHROPIC]: [
    'claude-3-opus',
    'claude-3-sonnet',
    'claude-3-haiku',
  ],
} as const;

// Supported File Types
export const SUPPORTED_FILE_TYPES = {
  IMAGES: ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
  DOCUMENTS: ['.txt', '.md', '.pdf', '.docx'],
  CODE: ['.js', '.ts', '.py', '.java', '.cpp', '.c', '.go', '.rs'],
  DATA: ['.json', '.csv', '.xml', '.yaml', '.yml'],
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK: 'Network error. Please check your connection.',
  TIMEOUT: 'Request timed out. Please try again.',
  UNAUTHORIZED: 'Invalid API key or unauthorized access.',
  RATE_LIMIT: 'Rate limit exceeded. Please try again later.',
  MODEL_NOT_AVAILABLE: 'Selected model is not available.',
  INVALID_INPUT: 'Invalid input provided.',
  STORAGE_FULL: 'Storage is full. Please clear some data.',
  UNKNOWN: 'An unexpected error occurred.',
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  MODEL_CONNECTED: 'Successfully connected to model',
  MESSAGE_SENT: 'Message sent successfully',
  DATA_SAVED: 'Data saved successfully',
  DATA_EXPORTED: 'Data exported successfully',
  HISTORY_CLEARED: 'Chat history cleared',
  API_KEY_SAVED: 'API key saved securely',
} as const;

// Theme Configuration
export const THEME_CONFIG = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

// Accessibility Configuration
export const A11Y_CONFIG = {
  FOCUS_VISIBLE_CLASS: 'keyboard-navigation',
  SKIP_LINK_TARGET: 'main-content',
  ARIA_LIVE_REGIONS: {
    POLITE: 'polite',
    ASSERTIVE: 'assertive',
    OFF: 'off',
  },
} as const;

// Feature Flags
export const FEATURE_FLAGS = {
  ENABLE_VOICE_INPUT: false,
  ENABLE_IMAGE_UPLOAD: false,
  ENABLE_EXPORT: true,
  ENABLE_THEMES: false,
  ENABLE_ANALYTICS: false,
} as const;

// Performance Configuration
export const PERFORMANCE_CONFIG = {
  VIRTUAL_LIST_ITEM_HEIGHT: 100,
  VIRTUAL_LIST_OVERSCAN: 5,
  DEBOUNCE_SEARCH: 300,
  THROTTLE_SCROLL: 16, // ~60fps
  LAZY_LOAD_THRESHOLD: '100px',
} as const;

// Security Configuration
export const SECURITY_CONFIG = {
  ENABLE_CSP: true,
  SANITIZE_HTML: true,
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_DOMAINS: [],
  BLOCKED_DOMAINS: [],
} as const;

// Development Configuration
export const DEV_CONFIG = {
  ENABLE_LOGGING: true,
  LOG_LEVEL: 'info',
  ENABLE_DEBUG_TOOLS: false,
  MOCK_API_RESPONSES: false,
} as const;

// Regular Expressions
export const REGEX_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  PHONE: /^\+?[\d\s\-\(\)]+$/,
  UUID: /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i,
  HEX_COLOR: /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/,
  SEMANTIC_VERSION: /^\d+\.\d+\.\d+$/,
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  CHAT_HISTORY: 'localai_chat_history',
  ACTIVE_MODEL: 'localai_active_model',
  API_KEYS: 'localai_api_keys',
  USER_PREFERENCES: 'localai_preferences',
  THEME: 'localai_theme',
  SIDEBAR_STATE: 'localai_sidebar_state',
  LAST_USED_PROVIDER: 'localai_last_provider',
} as const;

// Event Names
export const EVENT_NAMES = {
  MODEL_CONNECTED: 'model:connected',
  MODEL_DISCONNECTED: 'model:disconnected',
  MESSAGE_SENT: 'message:sent',
  MESSAGE_RECEIVED: 'message:received',
  ERROR_OCCURRED: 'error:occurred',
  THEME_CHANGED: 'theme:changed',
} as const;

// CSS Classes
export const CSS_CLASSES = {
  LOADING: 'loading',
  ERROR: 'error',
  SUCCESS: 'success',
  HIDDEN: 'hidden',
  VISIBLE: 'visible',
  DISABLED: 'disabled',
  ACTIVE: 'active',
  FOCUS_VISIBLE: 'keyboard-navigation',
} as const;