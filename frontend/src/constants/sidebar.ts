import type { Provider, ModelConfig } from '@/types/sidebar';

// Performance constants
export const PERFORMANCE = {
  VIRTUAL_SCROLL_THRESHOLD: 20,
  DEBOUNCE_DELAY: 300,
  ABORT_TIMEOUT: 10000,
} as const;

// CSS classes
export const SIDEBAR_STYLES = {
  BASE: 'h-screen border-r border-r-[#999999] bg-[#333333] text-white transition-all duration-400 flex flex-col',
  TOGGLE_BUTTON:
    'cursor-pointer p-4 border-b border-b-[#999999] focus:outline-none hover:bg-[#555555] transition-all duration-500',
  NAV_CONTAINER:
    'w-14 h-full bg-[#333333] text-white transition-all duration-400 flex-1',
  PANEL_BASE:
    'flex flex-col h-full border-l border-l-[#999999] overflow-hidden transition-all duration-300 ease-out',
  PANEL_OPEN: 'w-44 opacity-100',
  PANEL_CLOSED: 'w-0 opacity-0 pointer-events-none',
  ITEM_BUTTON:
    'flex justify-center items-center gap-2 py-4 px-1 hover:bg-[#555555] w-full cursor-pointer transition-all duration-500',
  ITEM_SELECTED: 'bg-[#555555]',
  MODEL_BUTTON:
    'flex items-center justify-center cursor-pointer w-full py-2 px-2 hover:bg-[#555555] transition-all duration-500',
  MODEL_SELECTED: 'bg-[#555555]',
  ERROR_TEXT: 'text-sm text-red-500 text-center p-2',
  SCROLL_CONTAINER: 'overflow-y-auto max-h-96',
  MODEL_COUNT: 'text-xs text-gray-400 px-2 py-1',
} as const;

// Default provider configurations
export const DEFAULT_PROVIDERS: Record<Provider, ModelConfig[]> = {
  ollama: [], // Will be populated dynamically
  openai: [
    {
      title: 'GPT-5 Nano',
      model: 'gpt-5-nano',
      provider: 'openai',
    },
    {
      title: 'GPT-4.1 Nano',
      model: 'gpt-4.1-nano',
      provider: 'openai',
    },
  ],
  anthropic: [
    {
      title: 'Claude 3 Opus',
      model: 'claude-3-opus-20240229',
      provider: 'anthropic',
    },
    {
      title: 'Claude 3 Sonnet',
      model: 'claude-3-sonnet-20240229',
      provider: 'anthropic',
    },
  ],
  google: [
    {
      title: 'Gemini Pro',
      model: 'gemini-pro',
      provider: 'google',
    },
    {
      title: 'Gemini Pro Vision',
      model: 'gemini-pro-vision',
      provider: 'google',
    },
  ],
} as const;

// Error messages
export const ERROR_MESSAGES = {
  OLLAMA_CONNECTION: 'Error getting models, check your ollama connection',
  OLLAMA_FETCH: 'Error fetching ollama models',
  MODEL_LOAD: 'Error loading models',
  NETWORK_ERROR: 'Network error occurred',
  TIMEOUT_ERROR: 'Request timed out',
  UNKNOWN_ERROR: 'An unknown error occurred',
} as const;

// Accessibility constants
export const ACCESSIBILITY = {
  LABELS: {
    TOGGLE_SIDEBAR: 'Toggle sidebar',
    SELECT_PROVIDER: 'Select provider',
    SELECT_MODEL: 'Select model',
    SIDEBAR_PANEL: 'Sidebar panel',
    MODEL_LIST: 'Available models',
    PROVIDER_LIST: 'Available providers',
  },
  ROLES: {
    NAVIGATION: 'navigation',
    LISTBOX: 'listbox',
    OPTION: 'option',
    BUTTON: 'button',
  },
  KEYS: {
    ESCAPE: 'Escape',
    ENTER: 'Enter',
    SPACE: ' ',
    ARROW_DOWN: 'ArrowDown',
    ARROW_UP: 'ArrowUp',
    TAB: 'Tab',
  },
} as const;

// Default state
export const DEFAULT_SIDEBAR_STATE = {
  isOpen: false,
  selectedProviderIndex: 0,
  selectedModelIndex: undefined,
  error: null,
} as const;
