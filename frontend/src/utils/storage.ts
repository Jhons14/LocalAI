import type { ChatMessage, ActiveModel } from '@/types/chat';

// Storage keys
const STORAGE_KEYS = {
  CHAT_HISTORY: 'localai_chat_history',
  ACTIVE_MODEL: 'localai_active_model',
  API_KEYS: 'localai_api_keys',
  USER_PREFERENCES: 'localai_preferences',
} as const;

// Storage configuration
const STORAGE_CONFIG = {
  MAX_MESSAGES_PER_THREAD: 1000,
  MAX_THREADS: 50,
  ENCRYPTION_ENABLED: false, // Could be enabled for sensitive data
} as const;

export interface StoredChatHistory {
  [threadId: string]: {
    messages: ChatMessage[];
    model: string;
    provider: string;
    lastUpdated: number;
    messageCount: number;
  };
}

export interface StoredUserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  autoSave: boolean;
  maxHistoryDays: number;
}

export class SecureStorage {
  private static isStorageAvailable(type: 'localStorage' | 'sessionStorage'): boolean {
    try {
      const storage = window[type];
      const testKey = '__storage_test__';
      storage.setItem(testKey, 'test');
      storage.removeItem(testKey);
      return true;
    } catch {
      return false;
    }
  }

  private static encrypt(data: string): string {
    // Simple encryption - in production, use proper encryption
    if (!STORAGE_CONFIG.ENCRYPTION_ENABLED) {
      return data;
    }
    return btoa(data);
  }

  private static decrypt(data: string): string {
    // Simple decryption - in production, use proper decryption
    if (!STORAGE_CONFIG.ENCRYPTION_ENABLED) {
      return data;
    }
    try {
      return atob(data);
    } catch {
      return data; // Return original if decryption fails
    }
  }

  static setItem(key: string, value: any, useSessionStorage = false): boolean {
    const storageType = useSessionStorage ? 'sessionStorage' : 'localStorage';
    
    if (!this.isStorageAvailable(storageType)) {
      console.warn(`${storageType} is not available`);
      return false;
    }

    try {
      const serialized = JSON.stringify(value);
      const encrypted = this.encrypt(serialized);
      window[storageType].setItem(key, encrypted);
      return true;
    } catch (error) {
      console.error(`Failed to save to ${storageType}:`, error);
      return false;
    }
  }

  static getItem<T>(key: string, defaultValue: T, useSessionStorage = false): T {
    const storageType = useSessionStorage ? 'sessionStorage' : 'localStorage';
    
    if (!this.isStorageAvailable(storageType)) {
      return defaultValue;
    }

    try {
      const encrypted = window[storageType].getItem(key);
      if (!encrypted) {
        return defaultValue;
      }

      const decrypted = this.decrypt(encrypted);
      return JSON.parse(decrypted);
    } catch (error) {
      console.error(`Failed to read from ${storageType}:`, error);
      return defaultValue;
    }
  }

  static removeItem(key: string, useSessionStorage = false): boolean {
    const storageType = useSessionStorage ? 'sessionStorage' : 'localStorage';
    
    if (!this.isStorageAvailable(storageType)) {
      return false;
    }

    try {
      window[storageType].removeItem(key);
      return true;
    } catch (error) {
      console.error(`Failed to remove from ${storageType}:`, error);
      return false;
    }
  }

  static clear(useSessionStorage = false): boolean {
    const storageType = useSessionStorage ? 'sessionStorage' : 'localStorage';
    
    if (!this.isStorageAvailable(storageType)) {
      return false;
    }

    try {
      window[storageType].clear();
      return true;
    } catch (error) {
      console.error(`Failed to clear ${storageType}:`, error);
      return false;
    }
  }
}

export class ChatHistoryStorage {
  static saveChatHistory(threadId: string, messages: ChatMessage[], model: string, provider: string): boolean {
    const history = this.getChatHistory();
    
    // Limit message count per thread
    const limitedMessages = messages.slice(-STORAGE_CONFIG.MAX_MESSAGES_PER_THREAD);
    
    history[threadId] = {
      messages: limitedMessages,
      model,
      provider,
      lastUpdated: Date.now(),
      messageCount: limitedMessages.length,
    };

    // Limit total number of threads
    const threadIds = Object.keys(history);
    if (threadIds.length > STORAGE_CONFIG.MAX_THREADS) {
      // Remove oldest threads
      const sortedThreads = threadIds
        .map(id => ({ id, lastUpdated: history[id].lastUpdated }))
        .sort((a, b) => a.lastUpdated - b.lastUpdated);
      
      const threadsToRemove = sortedThreads.slice(0, threadIds.length - STORAGE_CONFIG.MAX_THREADS);
      threadsToRemove.forEach(thread => {
        delete history[thread.id];
      });
    }

    return SecureStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, history);
  }

  static getChatHistory(): StoredChatHistory {
    return SecureStorage.getItem(STORAGE_KEYS.CHAT_HISTORY, {});
  }

  static getChatThread(threadId: string): ChatMessage[] {
    const history = this.getChatHistory();
    return history[threadId]?.messages || [];
  }

  static deleteChatThread(threadId: string): boolean {
    const history = this.getChatHistory();
    if (history[threadId]) {
      delete history[threadId];
      return SecureStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, history);
    }
    return true;
  }

  static clearAllChatHistory(): boolean {
    return SecureStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, {});
  }

  static getThreadList(): Array<{ id: string; model: string; provider: string; lastUpdated: number; messageCount: number }> {
    const history = this.getChatHistory();
    return Object.entries(history).map(([id, data]) => ({
      id,
      model: data.model,
      provider: data.provider,
      lastUpdated: data.lastUpdated,
      messageCount: data.messageCount,
    }));
  }
}

export class ModelStorage {
  static saveActiveModel(model: ActiveModel): boolean {
    return SecureStorage.setItem(STORAGE_KEYS.ACTIVE_MODEL, model);
  }

  static getActiveModel(): ActiveModel | null {
    return SecureStorage.getItem(STORAGE_KEYS.ACTIVE_MODEL, null);
  }

  static clearActiveModel(): boolean {
    return SecureStorage.removeItem(STORAGE_KEYS.ACTIVE_MODEL);
  }
}

export class ApiKeyStorage {
  static saveApiKey(provider: string, apiKey: string): boolean {
    const keys = this.getApiKeys();
    // Note: In production, API keys should be encrypted or not stored client-side
    keys[provider] = apiKey;
    return SecureStorage.setItem(STORAGE_KEYS.API_KEYS, keys, true); // Use sessionStorage for security
  }

  static getApiKey(provider: string): string | null {
    const keys = this.getApiKeys();
    return keys[provider] || null;
  }

  static getApiKeys(): Record<string, string> {
    return SecureStorage.getItem(STORAGE_KEYS.API_KEYS, {}, true);
  }

  static removeApiKey(provider: string): boolean {
    const keys = this.getApiKeys();
    if (keys[provider]) {
      delete keys[provider];
      return SecureStorage.setItem(STORAGE_KEYS.API_KEYS, keys, true);
    }
    return true;
  }

  static clearAllApiKeys(): boolean {
    return SecureStorage.setItem(STORAGE_KEYS.API_KEYS, {}, true);
  }
}

export class PreferencesStorage {
  static savePreferences(preferences: Partial<StoredUserPreferences>): boolean {
    const current = this.getPreferences();
    const updated = { ...current, ...preferences };
    return SecureStorage.setItem(STORAGE_KEYS.USER_PREFERENCES, updated);
  }

  static getPreferences(): StoredUserPreferences {
    return SecureStorage.getItem(STORAGE_KEYS.USER_PREFERENCES, {
      theme: 'system',
      language: 'en',
      autoSave: true,
      maxHistoryDays: 30,
    });
  }

  static clearPreferences(): boolean {
    return SecureStorage.removeItem(STORAGE_KEYS.USER_PREFERENCES);
  }
}

// Utility functions for data cleanup
export class StorageMaintenance {
  static cleanupOldData(): void {
    const preferences = PreferencesStorage.getPreferences();
    const maxAge = preferences.maxHistoryDays * 24 * 60 * 60 * 1000; // Convert to milliseconds
    const cutoffTime = Date.now() - maxAge;

    const history = ChatHistoryStorage.getChatHistory();
    let hasChanges = false;

    Object.keys(history).forEach(threadId => {
      if (history[threadId].lastUpdated < cutoffTime) {
        delete history[threadId];
        hasChanges = true;
      }
    });

    if (hasChanges) {
      SecureStorage.setItem(STORAGE_KEYS.CHAT_HISTORY, history);
    }
  }

  static getStorageUsage(): { used: number; available: number; percentage: number } {
    if (!SecureStorage.isStorageAvailable('localStorage')) {
      return { used: 0, available: 0, percentage: 0 };
    }

    let used = 0;
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        used += localStorage[key].length + key.length;
      }
    }

    // Most browsers allow ~5-10MB for localStorage
    const available = 5 * 1024 * 1024; // 5MB estimate
    const percentage = (used / available) * 100;

    return { used, available, percentage };
  }
}