/**
 * Centralized exports for all custom hooks
 */

// Core hooks
export { useAsync, useAsyncCallback } from './useAsync';
export { useDebounce, useDebouncedCallback, useThrottledCallback } from './useDebounce';
export { useLocalStorage } from './useLocalStorage';
export { useToggle, useBoolean } from './useToggle';
export { usePrevious, useCompare } from './usePrevious';

// UI/UX hooks
export { useKeyboard, useKeyPress, useEscapeKey, KEYBOARD_SHORTCUTS } from './useKeyboard';
export { useToast } from './useToast';
export { useMobileFirst, useTabletFirst, useBreakpoint } from './useResponsive';

// Business logic hooks
export { useChatHistoryContext } from './useChatHistoryContext';
export { useApi } from './useApi';
export { useChatApi } from './useChatApi';
export { useValidation } from './useValidation';

// Accessibility hooks
export { useAccessibility } from './useAccessibility';

// Storage hooks
export {
  usePersistentChatHistory,
  usePersistentActiveModel,
  usePersistentApiKeys,
  useStorageMaintenance,
  usePersistence,
} from './usePersistentState';