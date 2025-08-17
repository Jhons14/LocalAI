import { useState, useEffect, useCallback, useRef } from 'react';
import { useChatApi } from './useChatApi';
import { useToast } from './useToast';
import { errorLogger } from '@/utils';
import type { 
  NavigationItems, 
  NavigationItem, 
  ModelConfig, 
  UseSidebarDataResult,
  ModelsApiResponse,
  Provider 
} from '@/types/sidebar';
import { DEFAULT_PROVIDERS, ERROR_MESSAGES } from '@/constants/sidebar';

export const useSidebarData = (): UseSidebarDataResult => {
  const [navigationItems, setNavigationItems] = useState<NavigationItems>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const { getOllamaModels } = useChatApi();
  const { error: showError } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  const createNavigationItems = useCallback((ollamaModels: ModelConfig[] = []): NavigationItems => {
    return [
      {
        name: 'Ollama',
        icon: null, // Will be set in the component
        subItems: ollamaModels,
        isLoading: false,
        error: null,
      },
      {
        name: 'OpenAI',
        icon: null, // Will be set in the component
        subItems: DEFAULT_PROVIDERS.openai,
        isLoading: false,
        error: null,
      },
    ];
  }, []);

  const fetchOllamaModels = useCallback(async (): Promise<ModelConfig[]> => {
    try {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      const response = await getOllamaModels();
      
      if (!response) {
        throw new Error(ERROR_MESSAGES.OLLAMA_FETCH);
      }

      const ollamaModels: ModelConfig[] = response['ollama'].map((model: string) => ({
        title: model,
        model: model,
        provider: 'ollama' as Provider,
      }));

      return ollamaModels;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw err; // Re-throw abort errors to be handled by caller
      }
      
      errorLogger.error('Error fetching Ollama models:', err);
      const errorMessage = err.message || ERROR_MESSAGES.OLLAMA_CONNECTION;
      showError('Ollama Connection Error', errorMessage);
      throw new Error(errorMessage);
    }
  }, [getOllamaModels, showError]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const ollamaModels = await fetchOllamaModels();
      const items = createNavigationItems(ollamaModels);
      setNavigationItems(items);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMessage = err.message || ERROR_MESSAGES.MODEL_LOAD;
        setError(errorMessage);
        
        // Set navigation items with error state for Ollama
        const itemsWithError = createNavigationItems([]);
        itemsWithError[0] = {
          ...itemsWithError[0],
          error: errorMessage,
        };
        setNavigationItems(itemsWithError);
      }
    } finally {
      setIsLoading(false);
    }
  }, [fetchOllamaModels, createNavigationItems]);

  const refetch = useCallback(async () => {
    await loadData();
  }, [loadData]);

  // Initial load
  useEffect(() => {
    loadData();

    // Cleanup function
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [loadData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    navigationItems,
    isLoading,
    error,
    refetch,
  };
};