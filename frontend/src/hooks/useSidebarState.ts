import { useState, useCallback } from 'react';
import { useChatHistoryContext } from './useChatHistoryContext';
import type { 
  SidebarState, 
  SidebarActions, 
  UseSidebarStateResult, 
  ModelConfig 
} from '@/types/sidebar';
import { DEFAULT_SIDEBAR_STATE } from '@/constants/sidebar';

export const useSidebarState = (): UseSidebarStateResult => {
  const [state, setState] = useState<SidebarState>(DEFAULT_SIDEBAR_STATE);
  const { rechargeModel } = useChatHistoryContext();

  const toggleSidebar = useCallback(() => {
    setState(prev => ({ ...prev, isOpen: !prev.isOpen }));
  }, []);

  const selectProvider = useCallback((index: number) => {
    setState(prev => {
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

  const selectModel = useCallback((index: number, model: ModelConfig) => {
    setState(prev => {
      // Don't do anything if selecting the same model
      if (index === prev.selectedModelIndex) {
        return prev;
      }

      // Update the chat context with the new model
      rechargeModel(model.model, model.provider);

      return {
        ...prev,
        selectedModelIndex: index,
        error: null,
      };
    });
  }, [rechargeModel]);

  const setError = useCallback((error: string | null) => {
    setState(prev => ({ ...prev, error }));
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
  };
};