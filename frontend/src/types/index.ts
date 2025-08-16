/**
 * Main types index - Re-exports all types for easy importing
 */

// Chat related types
export type {
  ChatMessage,
  ActiveModel,
  ChatContextValue,
  SendMessageParams,
  ConfigureModelParams,
  ModelName,
  ModelProvider,
} from './chat';

// Component prop types
export type {
  ChatOutputProps,
  AssistantMessageOutputProps,
  UserMessageOutputProps,
  SidebarProps,
  SidebarItemProps,
  ToastProps,
  LoadingButtonProps,
  ConnectionStatusProps,
  ErrorBoundaryProps,
} from './components';

// API types
export type {
  HttpMethod,
  ApiResponse,
  ApiError,
  RequestConfig,
  StreamResponse,
  ApiEndpoints,
  ModelConfig,
  ChatRequest,
  ChatResponse,
  AvailableModel,
  ModelsResponse,
} from './api';

// UI types
export type {
  Theme,
  Size,
  ColorVariant,
  ButtonVariant,
  LoadingState,
  ToastType,
  ToastMessage,
  ModalProps,
  FormField,
  FormState,
  Breakpoint,
  BreakpointState,
  AnimationType,
  AnimationConfig,
  A11yProps,
  KeyHandler,
  DragItem,
  DropTarget,
  VirtualItem,
  VirtualListProps,
  SearchConfig,
  FilterConfig,
  SortConfig,
  PaginationConfig,
  PaginationState,
} from './ui';

// Event types
export type {
  CustomEvent,
  EventHandler,
  EventEmitter,
  AppEvent,
  StateChangeEvent,
  ErrorEvent,
  PerformanceEvent,
  UserInteractionEvent,
  AsyncOperationEvent,
  SubscriptionOptions,
  EventBus,
} from './events';