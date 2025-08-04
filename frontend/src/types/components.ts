import { JSX } from 'react';
import { ModelName, ModelProvider } from './chat';

export interface NavItem {
  name: string;
  icon: JSX.Element;
  subItems?: SubItem[];
}

export interface SubItem {
  title: string;
  model: ModelName;
  provider: ModelProvider;
  api_key?: string;
}

export interface SidebarItemProps {
  index: number;
  item: NavItem;
  isBarOpen: boolean;
  setIsBarOpen: (open: boolean) => void;
  isItemOpen: boolean;
  setIsItemOpen: (open: boolean) => void;
  selectedIndex: number | undefined;
  setSelectedIndex: (index: number | undefined) => void;
}

export interface ChatInputProps {
  thread_id?: string;
}

export interface ChatOutputProps {
  thread_id?: string;
}

export interface UserMessageOutputProps {
  msg: {
    id: string;
    content?: string;
    status?: 'complete' | 'streaming' | 'error';
  };
  thread_id?: string;
}

export interface AssistantMessageOutputProps {
  content?: string;
}

export interface ApiKeyInputProps {
  model: string;
  provider: string;
}