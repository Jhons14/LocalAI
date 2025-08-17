import type { JSX } from 'react';

// Core provider and model types
export type Provider = 'ollama' | 'openai' | 'anthropic' | 'google';

export type ModelName = string; // Dynamic model names from API

export interface ModelConfig {
  title: string;
  model: ModelName;
  provider: Provider;
  api_key?: string;
}

// Navigation item types
export interface NavigationItem {
  name: string;
  icon: JSX.Element | null;
  subItems?: ModelConfig[];
  isLoading?: boolean;
  error?: string | null;
}

export type NavigationItems = NavigationItem[];

// Sidebar state interfaces
export interface SidebarState {
  isOpen: boolean;
  selectedProviderIndex: number;
  selectedModelIndex?: number;
  error: string | null;
}

export interface SidebarActions {
  toggleSidebar: () => void;
  selectProvider: (index: number) => void;
  selectModel: (index: number, model: ModelConfig) => void;
  setError: (error: string | null) => void;
  reset: () => void;
  syncWithActiveModel: () => void;
}

// Component prop interfaces
export interface SidebarProps {
  className?: string;
}

export interface SidebarHeaderProps {
  isOpen: boolean;
  onToggle: () => void;
}

export interface SidebarNavigationProps {
  items: NavigationItems;
  selectedIndex: number;
  isOpen: boolean;
  onItemSelect: (index: number) => void;
  onToggle: () => void;
}

export interface SidebarPanelProps {
  isOpen: boolean;
  selectedItem: NavigationItem | null;
  selectedModelIndex?: number;
  onModelSelect: (index: number, model: ModelConfig) => void;
}

export interface ModelListProps {
  models: ModelConfig[];
  selectedIndex?: number;
  onModelSelect: (index: number, model: ModelConfig) => void;
  isLoading?: boolean;
  error?: string | null;
  maxItemsBeforeVirtualization?: number;
}

export interface ModelItemProps {
  model: ModelConfig;
  index: number;
  isSelected: boolean;
  onClick: (index: number, model: ModelConfig) => void;
}

export interface SidebarItemProps {
  item: NavigationItem;
  index: number;
  isOpen: boolean;
  isSelected: boolean;
  onSelect: (index: number) => void;
  onToggle: () => void;
}

// Hook interfaces
export interface UseSidebarDataResult {
  navigationItems: NavigationItems;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export interface UseSidebarStateResult extends SidebarState, SidebarActions {}

// API response types
export interface ModelsApiResponse {
  [provider: string]: string[];
}

// Error types
export interface SidebarError {
  provider: Provider;
  message: string;
  timestamp: Date;
}

// Accessibility types
export interface AccessibilityConfig {
  enableKeyboardNavigation: boolean;
  announceSelections: boolean;
  customAriaLabels?: {
    [key: string]: string;
  };
}