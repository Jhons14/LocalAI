import { useState, useEffect, useCallback, useRef } from 'react';
import { useChatApi } from './useChatApi';
import { useToast } from './useToast';
import { errorLogger } from '@/utils';
import type {
  NavigationItems,
  ModelConfig,
  UseSidebarDataResult,
  Provider,
} from '@/types/sidebar';
import { getProviderIcon } from '@/utils/providerIcons';
import { DEFAULT_PROVIDERS, ERROR_MESSAGES } from '@/constants/sidebar';

export const useSidebarData = (): UseSidebarDataResult => {
  const [navigationItems, setNavigationItems] = useState<NavigationItems>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { getOllamaModels } = useChatApi();
  const { error: showError } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  const cloudNavItems = [
    {
      name: 'OpenAI',
      icon: getProviderIcon('openai'), // Will be set in the component
      subItems: DEFAULT_PROVIDERS.openai,
      isLoading: false,
      error: null,
    },
    {
      name: 'Anthropic',
      icon: getProviderIcon('anthropic'), // Will be set in the component
      subItems: DEFAULT_PROVIDERS.anthropic,
      isLoading: false,
      error: null,
    },
    {
      name: 'Google',
      icon: getProviderIcon('google'), // Will be set in the component
      subItems: DEFAULT_PROVIDERS.google,
      isLoading: false,
      error: null,
    },
  ];

  const createNavigationItems = useCallback(
    (ollamaModels: ModelConfig[] = []): NavigationItems => {
      return [
        ...cloudNavItems,
        {
          name: 'Ollama',
          icon: getProviderIcon('ollama'),
          subItems: ollamaModels,
          isLoading: false,
          error: null,
        },
      ];
    },
    []
  );

  if (navigationItems.length === 0)
    setNavigationItems(createNavigationItems([]));

  const fetchOllamaModels = useCallback(async (): Promise<ModelConfig[]> => {
    try {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      const response = await getOllamaModels();

      if (!response['ollama']) {
        throw new Error(ERROR_MESSAGES.OLLAMA_FETCH);
      }

      const ollamaModels: ModelConfig[] = response['ollama'].map(
        (model: string) => ({
          title: model,
          model: model,
          provider: 'ollama' as Provider,
        })
      );

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
        console.log(itemsWithError);
        const navItemsWithOllamaError = itemsWithError.map((item) => {
          if (item.name === 'Ollama') {
            return {
              ...item,
              error: errorMessage,
            };
          } else {
            return item;
          }
        });

        setNavigationItems(navItemsWithOllamaError);
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
