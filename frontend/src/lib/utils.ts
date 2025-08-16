import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Re-export common utilities for backward compatibility
export {
  truncateText,
  capitalizeFirstLetter,
  formatDate,
  formatRelativeTime,
  formatBytes,
  copyToClipboard,
  downloadFile,
  debounce,
  throttle,
  sleep,
  retry,
} from '@/utils/common';

export {
  API_CONFIG,
  UI_CONFIG,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
} from '@/utils/constants';
