import type { ActiveModel, ModelProvider } from '@/types/chat';
import type { NavigationItems, ModelConfig } from '@/types/sidebar';

/**
 * Maps an active model to sidebar provider and model indices
 */
export function getModelIndices(
  activeModel: ActiveModel | null | undefined,
  navigationItems: NavigationItems
): { providerIndex: number; modelIndex: number | undefined } {
  if (!activeModel || !navigationItems.length) {
    return { providerIndex: 0, modelIndex: undefined };
  }

  // Find provider index
  const providerIndex = navigationItems.findIndex(
    (item) => item.name.toLowerCase() === activeModel.provider?.toLowerCase()
  );

  if (providerIndex === -1) {
    return { providerIndex: 0, modelIndex: undefined };
  }

  // Find model index within the provider's subItems
  const provider = navigationItems[providerIndex];
  if (!provider?.subItems || !provider.subItems.length) {
    return { providerIndex, modelIndex: undefined };
  }

  const modelIndex = provider.subItems.findIndex(
    (model) => model.model === activeModel.model
  );

  return {
    providerIndex,
    modelIndex: modelIndex === -1 ? undefined : modelIndex,
  };
}

/**
 * Gets the model config from sidebar indices
 */
export function getModelFromIndices(
  providerIndex: number,
  modelIndex: number | undefined,
  navigationItems: NavigationItems
): ModelConfig | null {
  if (!navigationItems[providerIndex] || modelIndex === undefined) {
    return null;
  }

  const provider = navigationItems[providerIndex];
  if (!provider.subItems || !provider.subItems[modelIndex]) {
    return null;
  }

  return provider.subItems[modelIndex];
}

/**
 * Validates if a model exists in the navigation items
 */
export function validateModel(
  activeModel: ActiveModel | null | undefined,
  navigationItems: NavigationItems
): boolean {
  if (!activeModel || !navigationItems.length) {
    return false;
  }

  const { providerIndex, modelIndex } = getModelIndices(activeModel, navigationItems);
  
  const provider = navigationItems[providerIndex];
  return !!(providerIndex >= 0 &&
    providerIndex < navigationItems.length &&
    modelIndex !== undefined &&
    provider?.subItems &&
    modelIndex < provider.subItems.length);
}

/**
 * Gets the default model when no valid active model exists
 */
export function getDefaultModel(navigationItems: NavigationItems): ModelConfig | null {
  // Try to find Ollama provider first (index should be 3 based on useSidebarData)
  const ollamaProvider = navigationItems.find(item => item.name === 'Ollama');
  if (ollamaProvider?.subItems && ollamaProvider.subItems.length > 0) {
    return ollamaProvider.subItems[0] ?? null;
  }

  // Fallback to first available model
  for (const provider of navigationItems) {
    if (provider?.subItems && provider.subItems.length > 0) {
      return provider.subItems[0] ?? null;
    }
  }

  return null;
}