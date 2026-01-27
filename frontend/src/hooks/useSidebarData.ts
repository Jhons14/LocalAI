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

// Provider order for consistent display
const PROVIDER_ORDER: Provider[] = ['openai', 'anthropic', 'google', 'ollama'];

interface ProviderResponse {
  name: string;
  requires_api_key: boolean;
  models: Array<{
    title: string;
    model: string;
    provider: string;
  }>;
  error?: string;
}

interface ProvidersApiResponse {
  [key: string]: ProviderResponse;
}

export const useSidebarData = (): UseSidebarDataResult => {
  const [navigationItems, setNavigationItems] = useState<NavigationItems>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { getProviders } = useChatApi();
  const { error: showError } = useToast();
  const abortControllerRef = useRef<AbortController | null>(null);

  // Create navigation items from API response
  const createNavigationItemsFromApi = useCallback(
    (providersData: ProvidersApiResponse): NavigationItems => {
      const items: NavigationItems = [];

      for (const providerKey of PROVIDER_ORDER) {
        const providerData = providersData[providerKey];

        if (providerData) {
          const models: ModelConfig[] = providerData.models.map((m) => ({
            title: m.title,
            model: m.model,
            provider: m.provider as Provider,
          }));

          items.push({
            name: providerData.name,
            icon: getProviderIcon(providerKey),
            subItems: models,
            isLoading: false,
            error: providerData.error || null,
          });
        }
      }

      return items;
    },
    []
  );

  // Create fallback navigation items using DEFAULT_PROVIDERS
  const createFallbackNavigationItems = useCallback((): NavigationItems => {
    return PROVIDER_ORDER.map((providerKey) => ({
      name: providerKey.charAt(0).toUpperCase() + providerKey.slice(1),
      icon: getProviderIcon(providerKey),
      subItems: DEFAULT_PROVIDERS[providerKey] || [],
      isLoading: false,
      error: null,
    }));
  }, []);

  // Initialize with fallback items
  if (navigationItems.length === 0) {
    setNavigationItems(createFallbackNavigationItems());
  }

  const fetchProviders = useCallback(async (): Promise<ProvidersApiResponse> => {
    try {
      // Cancel previous request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new abort controller
      abortControllerRef.current = new AbortController();

      const response = await getProviders();
      return response as ProvidersApiResponse;
    } catch (err: any) {
      if (err.name === 'AbortError') {
        throw err;
      }

      errorLogger.error('Error fetching providers:', err);
      const errorMessage = err.message || ERROR_MESSAGES.MODEL_LOAD;
      showError('Provider Connection Error', errorMessage);
      throw new Error(errorMessage);
    }
  }, [getProviders, showError]);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const providersData = await fetchProviders();
      const items = createNavigationItemsFromApi(providersData);

      setNavigationItems(items);
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        const errorMessage = err.message || ERROR_MESSAGES.MODEL_LOAD;
        setError(errorMessage);

        // Use fallback navigation items with error state
        const fallbackItems = createFallbackNavigationItems();
        setNavigationItems(fallbackItems);
      }
    } finally {
      setIsLoading(false);
    }
  }, [fetchProviders, createNavigationItemsFromApi, createFallbackNavigationItems]);

  const refetch = useCallback(async () => {
    await loadData();
  }, [loadData]);

  // Initial load
  useEffect(() => {
    loadData();

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
