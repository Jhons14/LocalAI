export type MessageRole = 'user' | 'assistant';
export type MessageStatus = 'complete' | 'streaming' | 'error';
export type ModelProvider = 'ollama' | 'openai';
export type ModelName = 'qwen2.5:3b' | 'gpt-4.1-nano' | 'qwen3:1.7b';
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
}
