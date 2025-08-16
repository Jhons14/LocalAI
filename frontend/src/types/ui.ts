/**
 * UI and interaction related types
 */

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// Size variants
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

// Color variants
export type ColorVariant = 
  | 'primary' 
  | 'secondary' 
  | 'success' 
  | 'warning' 
  | 'error' 
  | 'info';

// Button variants
export type ButtonVariant = 
  | 'solid' 
  | 'outline' 
  | 'ghost' 
  | 'link';

// Loading states
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

// Toast types
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
}

// Modal props
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  size?: Size;
  closeOnOverlayClick?: boolean;
  closeOnEscape?: boolean;
}

// Form field types
export interface FormField<T = any> {
  value: T;
  error?: string;
  touched: boolean;
  dirty: boolean;
}

export interface FormState<T extends Record<string, any>> {
  fields: {
    [K in keyof T]: FormField<T[K]>;
  };
  isValid: boolean;
  isSubmitting: boolean;
  isDirty: boolean;
}

// Breakpoint types
export type Breakpoint = 'mobile' | 'tablet' | 'desktop' | 'wide';

export interface BreakpointState {
  mobile: boolean;
  tablet: boolean;
  desktop: boolean;
  wide: boolean;
  current: Breakpoint;
}

// Animation types
export type AnimationType = 
  | 'fade' 
  | 'slide' 
  | 'scale' 
  | 'bounce' 
  | 'flip';

export interface AnimationConfig {
  type: AnimationType;
  duration: number;
  delay?: number;
  easing?: string;
}

// Accessibility types
export interface A11yProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  role?: string;
}

// Key handler types
export interface KeyHandler {
  key: string;
  ctrlKey?: boolean;
  shiftKey?: boolean;
  altKey?: boolean;
  metaKey?: boolean;
  handler: (event: KeyboardEvent) => void;
}

// Drag and drop types
export interface DragItem {
  id: string;
  type: string;
  data: any;
}

export interface DropTarget {
  id: string;
  accepts: string[];
  onDrop: (item: DragItem) => void;
}

// Virtual list types
export interface VirtualItem {
  id: string;
  height: number;
  offset: number;
  data: any;
}

export interface VirtualListProps {
  items: any[];
  itemHeight: number | ((index: number, item: any) => number);
  containerHeight: number;
  overscan?: number;
  renderItem: (item: any, index: number) => React.ReactNode;
}

// Search and filter types
export interface SearchConfig {
  query: string;
  fields: string[];
  caseSensitive?: boolean;
  fuzzy?: boolean;
  highlight?: boolean;
}

export interface FilterConfig {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'contains' | 'startsWith' | 'endsWith';
  value: any;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

// Pagination types
export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
}

export interface PaginationState extends PaginationConfig {
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
}