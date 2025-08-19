export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'complete' | 'streaming' | 'error' | 'interrupted';
export type ModelProvider = 'ollama' | 'openai' | 'anthropic' | 'google';
export type ModelName = string; // Dynamic model names from API
export type ToolName = 'Gmail' | 'Asana';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  status?: MessageStatus;
  relatedTo?: string;
  edited?: boolean;
  createdAt: number;
  thread_id?: string;
  model?: ModelName;
  provider?: ModelProvider;
}

export interface ActiveModel {
  thread_id: string;
  model: ModelName;
  provider: ModelProvider;
  apiKey?: string | null;
  toolkits: string[];
}

export interface SendMessageParams {
  content: string;
  thread_id: string;
  model: ModelName;
  provider: ModelProvider;
  api_key?: string | undefined;
  toolkits: string[];
  enable_memory?: boolean;
  email?: string;
}

export interface ConfigureModelParams {
  model: ModelName;
  provider: ModelProvider;
  connectModel?: boolean;
  thread_id: string;
}
export interface AddToolToModelParams {
  thread_id: string;
}
export interface ChatContextValue {
  messages: ChatMessage[];
  sendMessage: (params: SendMessageParams) => void;
  edit: (userMessageId: string, newContent: string, thread_id: string) => void;
  clear: () => void;
  activeModel: ActiveModel | undefined;
  setActiveModel: React.Dispatch<React.SetStateAction<ActiveModel | undefined>>;
  tempApiKey: string;
  setTempApiKey: (tempApiKey: string) => void;
  isModelConnected: boolean;
  setIsModelConnected: (isModelConnected: boolean) => void;
  rechargeModel: (model: string, provider: ModelProvider) => void;
  isStreaming: boolean;
  userEmail: string;
  setUserEmail: (email: string) => void;
}
