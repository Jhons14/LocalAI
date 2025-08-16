import { useState, useEffect, useCallback, useRef } from 'react';
import { ChatHistoryStorage, ModelStorage, ApiKeyStorage, StorageMaintenance } from '@/utils/storage';
import type { ChatMessage, ActiveModel } from '@/types/chat';
import { useToast } from './useToast';

export function usePersistentChatHistory() {
  const { info } = useToast();
  const autoSaveTimeoutRef = useRef<NodeJS.Timeout>();

  const saveChatHistory = useCallback((
    threadId: string, 
    messages: ChatMessage[], 
    model: string, 
    provider: string
  ) => {
    // Debounce auto-save to avoid excessive writes
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    autoSaveTimeoutRef.current = setTimeout(() => {
      const success = ChatHistoryStorage.saveChatHistory(threadId, messages, model, provider);
      if (!success) {
        console.warn('Failed to save chat history to storage');
      }
    }, 1000); // 1 second debounce
  }, []);

  const loadChatHistory = useCallback((threadId: string): ChatMessage[] => {
    return ChatHistoryStorage.getChatThread(threadId);
  }, []);

  const getAllThreads = useCallback(() => {
    return ChatHistoryStorage.getThreadList();
  }, []);

  const deleteChatThread = useCallback((threadId: string) => {
    const success = ChatHistoryStorage.deleteChatThread(threadId);
    if (success) {
      info('Thread Deleted', 'Chat history has been removed');
    }
    return success;
  }, [info]);

  const clearAllHistory = useCallback(() => {
    const success = ChatHistoryStorage.clearAllChatHistory();
    if (success) {
      info('History Cleared', 'All chat history has been cleared');
    }
    return success;
  }, [info]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, []);

  return {
    saveChatHistory,
    loadChatHistory,
    getAllThreads,
    deleteChatThread,
    clearAllHistory,
  };
}

export function usePersistentActiveModel() {
  const [activeModel, setActiveModelState] = useState<ActiveModel | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load active model on mount
  useEffect(() => {
    const savedModel = ModelStorage.getActiveModel();
    if (savedModel) {
      setActiveModelState(savedModel);
    }
    setIsLoaded(true);
  }, []);

  const setActiveModel = useCallback((model: ActiveModel | null) => {
    setActiveModelState(model);
    
    if (model) {
      ModelStorage.saveActiveModel(model);
    } else {
      ModelStorage.clearActiveModel();
    }
  }, []);

  const clearActiveModel = useCallback(() => {
    setActiveModelState(null);
    ModelStorage.clearActiveModel();
  }, []);

  return {
    activeModel,
    setActiveModel,
    clearActiveModel,
    isLoaded,
  };
}

export function usePersistentApiKeys() {
  const [apiKeys, setApiKeysState] = useState<Record<string, string>>({});
  const { success, error } = useToast();

  // Load API keys on mount
  useEffect(() => {
    const savedKeys = ApiKeyStorage.getApiKeys();
    setApiKeysState(savedKeys);
  }, []);

  const saveApiKey = useCallback((provider: string, apiKey: string) => {
    const success_result = ApiKeyStorage.saveApiKey(provider, apiKey);
    if (success_result) {
      setApiKeysState(prev => ({ ...prev, [provider]: apiKey }));
      success('API Key Saved', `${provider} API key has been securely saved`);
    } else {
      error('Save Failed', 'Failed to save API key');
    }
    return success_result;
  }, [success, error]);

  const getApiKey = useCallback((provider: string): string | null => {
    return apiKeys[provider] || null;
  }, [apiKeys]);

  const removeApiKey = useCallback((provider: string) => {
    const success_result = ApiKeyStorage.removeApiKey(provider);
    if (success_result) {
      setApiKeysState(prev => {
        const updated = { ...prev };
        delete updated[provider];
        return updated;
      });
      success('API Key Removed', `${provider} API key has been removed`);
    } else {
      error('Remove Failed', 'Failed to remove API key');
    }
    return success_result;
  }, [success, error]);

  const clearAllApiKeys = useCallback(() => {
    const success_result = ApiKeyStorage.clearAllApiKeys();
    if (success_result) {
      setApiKeysState({});
      success('API Keys Cleared', 'All API keys have been removed');
    } else {
      error('Clear Failed', 'Failed to clear API keys');
    }
    return success_result;
  }, [success, error]);

  return {
    apiKeys,
    saveApiKey,
    getApiKey,
    removeApiKey,
    clearAllApiKeys,
  };
}

export function useStorageMaintenance() {
  const { info, warning } = useToast();

  const cleanupOldData = useCallback(() => {
    try {
      StorageMaintenance.cleanupOldData();
      info('Storage Cleaned', 'Old chat history has been removed');
    } catch (error) {
      console.error('Failed to cleanup storage:', error);
    }
  }, [info]);

  const getStorageUsage = useCallback(() => {
    return StorageMaintenance.getStorageUsage();
  }, []);

  const checkStorageUsage = useCallback(() => {
    const usage = getStorageUsage();
    if (usage.percentage > 80) {
      warning(
        'Storage Almost Full',
        `Storage is ${usage.percentage.toFixed(1)}% full. Consider clearing old chat history.`
      );
    }
    return usage;
  }, [getStorageUsage, warning]);

  // Auto-cleanup on mount
  useEffect(() => {
    // Run cleanup on app start
    const timer = setTimeout(() => {
      cleanupOldData();
      checkStorageUsage();
    }, 2000); // Delay to avoid blocking initial render

    return () => clearTimeout(timer);
  }, [cleanupOldData, checkStorageUsage]);

  return {
    cleanupOldData,
    getStorageUsage,
    checkStorageUsage,
  };
}

// Combined hook for full persistence management
export function usePersistence() {
  const chatHistory = usePersistentChatHistory();
  const activeModel = usePersistentActiveModel();
  const apiKeys = usePersistentApiKeys();
  const maintenance = useStorageMaintenance();

  const isFullyLoaded = activeModel.isLoaded;

  const exportData = useCallback(() => {
    const threads = chatHistory.getAllThreads();
    const data = {
      threads,
      activeModel: activeModel.activeModel,
      preferences: {
        exportedAt: new Date().toISOString(),
        version: '1.0',
      },
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `localai-export-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [chatHistory, activeModel]);

  return {
    ...chatHistory,
    ...activeModel,
    ...apiKeys,
    ...maintenance,
    isFullyLoaded,
    exportData,
  };
}