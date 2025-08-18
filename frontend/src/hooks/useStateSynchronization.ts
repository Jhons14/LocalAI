import { useEffect, useCallback, useRef } from 'react';
import { useChatHistoryContext } from './useChatHistoryContext';
import { useSidebarData } from './useSidebarData';
import { useLoadingCoordinator } from './useLoadingCoordinator';
import type { ActiveModel } from '@/types/chat';
import type { NavigationItems } from '@/types/sidebar';
import {
  getModelIndices,
  validateModel,
  getDefaultModel,
} from '@/utils/modelMapping';

/**
 * Central state synchronization hook that ensures all UI states
 * stay synchronized with the persistent active model
 */
export function useStateSynchronization() {
  const { activeModel, setActiveModel } = useChatHistoryContext();
  const { navigationItems, isLoading: sidebarLoading } = useSidebarData();
  const loadingCoordinator = useLoadingCoordinator();
  const previousModelRef = useRef<ActiveModel | undefined>(activeModel);
  const isInitializedRef = useRef(false);

  // Determine overall loading state
  const isLoading = sidebarLoading || loadingCoordinator.isLoading;

  // Synchronize sidebar state with active model
  const syncSidebarWithActiveModel = useCallback(
    (model: ActiveModel | undefined, navItems: NavigationItems) => {
      if (!model || !navItems.length || isLoading) {
        return null;
      }

      const { providerIndex, modelIndex } = getModelIndices(model, navItems);

      return {
        providerIndex,
        modelIndex,
        isValid: validateModel(model, navItems),
      };
    },
    [isLoading]
  );

  // Coordinate loading phases
  useEffect(() => {
    if (
      !isInitializedRef.current &&
      !sidebarLoading &&
      navigationItems.length === 0
    ) {
      loadingCoordinator.startInitialization();
    } else if (
      !sidebarLoading &&
      navigationItems.length > 0 &&
      !loadingCoordinator.canProceedFromPhase('loading-models')
    ) {
      loadingCoordinator.startModelLoading();
    }
  }, [sidebarLoading, navigationItems.length, loadingCoordinator]);

  // Handle initialization and model validation
  useEffect(() => {
    if (sidebarLoading || !navigationItems.length) {
      return;
    }

    // Start state syncing phase
    if (!loadingCoordinator.canProceedFromPhase('syncing-state')) {
      loadingCoordinator.startStateSyncing();
    }

    // First time initialization
    if (!isInitializedRef.current) {
      isInitializedRef.current = true;

      // If no active model exists, set a default one
      if (!activeModel) {
        const defaultModel = getDefaultModel(navigationItems);
        if (defaultModel) {
          setActiveModel({
            model: defaultModel.model,
            provider: defaultModel.provider,
            thread_id: `thread-${Date.now()}`,
            toolkits: [],
          });
        }
        // Mark as ready after setting default model
        setTimeout(() => loadingCoordinator.markReady(), 100);
        return;
      }

      // Validate existing active model
      if (!validateModel(activeModel, navigationItems)) {
        console.warn(
          'Active model not found in navigation items, setting default'
        );
        const defaultModel = getDefaultModel(navigationItems);
        if (defaultModel) {
          setActiveModel({
            model: defaultModel.model,
            provider: defaultModel.provider,
            thread_id: activeModel.thread_id || `thread-${Date.now()}`,
            toolkits: activeModel.toolkits || [],
          });
        }
      }

      // Mark as ready after initialization
      setTimeout(() => loadingCoordinator.markReady(), 100);
    }

    // Track model changes for debugging
    if (previousModelRef.current !== activeModel) {
      previousModelRef.current = activeModel;
    }
  }, [
    activeModel,
    navigationItems,
    sidebarLoading,
    setActiveModel,
    loadingCoordinator,
  ]);

  // Validate model when navigation items change (e.g., Ollama models loaded)
  useEffect(() => {
    if (
      !activeModel ||
      isLoading ||
      !navigationItems.length ||
      !isInitializedRef.current
    ) {
      return;
    }

    // Re-validate model when navigation items change
    if (!validateModel(activeModel, navigationItems)) {
      console.warn('Active model became invalid after navigation items update');
      const defaultModel = getDefaultModel(navigationItems);
      if (defaultModel) {
        setActiveModel({
          model: defaultModel.model,
          provider: defaultModel.provider,
          thread_id: activeModel.thread_id || `thread-${Date.now()}`,
          toolkits: activeModel.toolkits || [],
        });
      }
    }
  }, [navigationItems, activeModel, isLoading, setActiveModel]);

  // Force sync function for manual synchronization
  const forceSyncStates = useCallback(() => {
    if (!activeModel || !navigationItems.length || isLoading) {
      return;
    }

    // Validate and potentially fix the active model
    if (!validateModel(activeModel, navigationItems)) {
      const defaultModel = getDefaultModel(navigationItems);
      if (defaultModel) {
        setActiveModel({
          model: defaultModel.model,
          provider: defaultModel.provider,
          thread_id: activeModel.thread_id || `thread-${Date.now()}`,
          toolkits: activeModel.toolkits || [],
        });
      }
    }
  }, [activeModel, navigationItems, isLoading, setActiveModel]);

  // Get current synchronization state
  const getSyncState = useCallback(() => {
    const sidebarSync = syncSidebarWithActiveModel(
      activeModel,
      navigationItems
    );

    return {
      activeModel,
      navigationItems,
      isLoading,
      isInitialized: isInitializedRef.current,
      sidebarSync,
      canSync: !isLoading && navigationItems.length > 0,
    };
  }, [activeModel, navigationItems, isLoading, syncSidebarWithActiveModel]);

  return {
    // Current state
    activeModel,
    navigationItems,
    isLoading,
    isInitialized: isInitializedRef.current,

    // Sync utilities
    syncSidebarWithActiveModel,
    forceSyncStates,
    getSyncState,

    // Validation utilities
    validateActiveModel: (model: ActiveModel) =>
      validateModel(model, navigationItems),
    getDefaultModel: () => getDefaultModel(navigationItems),
  };
}
