import { useState, useCallback, useEffect } from 'react';
import { useChatHistoryContext } from './useChatHistoryContext';
import { useStateSynchronization } from './useStateSynchronization';
import type {
  SidebarState,
  SidebarActions,
  UseSidebarStateResult,
  ModelConfig,
} from '@/types/sidebar';
import { DEFAULT_SIDEBAR_STATE } from '@/constants/sidebar';
import { getModelIndices } from '@/utils/modelMapping';

export const useSidebarState = (): UseSidebarStateResult => {
  const [state, setState] = useState<SidebarState>(DEFAULT_SIDEBAR_STATE);
  const { rechargeModel } = useChatHistoryContext();
  const { 
    activeModel, 
    navigationItems, 
    isLoading, 
    isInitialized,
    syncSidebarWithActiveModel 
  } = useStateSynchronization();

  // Synchronize sidebar state with active model when it changes
  useEffect(() => {
    if (!isInitialized || !activeModel || isLoading || !navigationItems.length) {
      return;
    }

    const syncResult = syncSidebarWithActiveModel(activeModel, navigationItems);
    
    if (!syncResult?.isValid) {
      console.warn('Active model not found in navigation items:', activeModel);
      return;
    }

    const { providerIndex, modelIndex } = syncResult;
    
    setState(prev => {
      // Only update if the indices are different to avoid unnecessary re-renders
      if (prev.selectedProviderIndex !== providerIndex || prev.selectedModelIndex !== modelIndex) {
        return {
          ...prev,
          selectedProviderIndex: providerIndex,
          selectedModelIndex: modelIndex,
          error: null,
        };
      }
      return prev;
    });
  }, [activeModel, navigationItems, isLoading, isInitialized, syncSidebarWithActiveModel]);

  const toggleSidebar = useCallback(() => {
    setState((prev) => ({ ...prev, isOpen: !prev.isOpen }));
  }, []);

  const selectProvider = useCallback((index: number) => {
    setState((prev) => {
      // If selecting the same provider, just toggle sidebar
      if (index === prev.selectedProviderIndex) {
        return { ...prev, isOpen: !prev.isOpen };
      }

      // If selecting different provider, open sidebar and reset model selection
      return {
        ...prev,
        selectedProviderIndex: index,
        selectedModelIndex: undefined,
        isOpen: true,
        error: null,
      };
    });
  }, []);

  const selectModel = useCallback(
    (index: number, model: ModelConfig) => {
      setState((prev) => {
        // Don't do anything if selecting the same model
        if (index === prev.selectedModelIndex) {
          return prev;
        }

        // Update the chat context with the new model
        // The activeModel will be updated, which will trigger the useEffect above
        rechargeModel(model.model, model.provider);

        return {
          ...prev,
          selectedModelIndex: index,
          error: null,
        };
      });
    },
    [rechargeModel]
  );

  // Add method to programmatically sync sidebar with active model
  const syncWithActiveModel = useCallback(() => {
    if (!activeModel || !navigationItems.length) {
      return;
    }

    const { providerIndex, modelIndex } = getModelIndices(activeModel, navigationItems);
    setState(prev => ({
      ...prev,
      selectedProviderIndex: providerIndex,
      selectedModelIndex: modelIndex,
      error: null,
    }));
  }, [activeModel, navigationItems]);

  const setError = useCallback((error: string | null) => {
    setState((prev) => ({ ...prev, error }));
  }, []);

  const reset = useCallback(() => {
    setState(DEFAULT_SIDEBAR_STATE);
  }, []);

  return {
    ...state,
    toggleSidebar,
    selectProvider,
    selectModel,
    setError,
    reset,
    syncWithActiveModel,
  };
};
