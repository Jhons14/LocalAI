import { useState, useEffect, useCallback, useRef } from 'react';

interface LoadingState {
  isLoading: boolean;
  phase: 'idle' | 'initializing' | 'loading-models' | 'syncing-state' | 'ready';
  error: string | null;
}

/**
 * Coordinates loading phases to prevent race conditions during app initialization
 */
export function useLoadingCoordinator() {
  const [loadingState, setLoadingState] = useState<LoadingState>({
    isLoading: true,
    phase: 'idle',
    error: null,
  });

  const initTimeoutRef = useRef<NodeJS.Timeout>();
  const phaseStartTimeRef = useRef<number>(0);

  // Start initialization phase
  const startInitialization = useCallback(() => {
    phaseStartTimeRef.current = Date.now();
    setLoadingState({
      isLoading: true,
      phase: 'initializing',
      error: null,
    });
  }, []);

  // Start model loading phase
  const startModelLoading = useCallback(() => {
    phaseStartTimeRef.current = Date.now();
    setLoadingState(prev => ({
      ...prev,
      phase: 'loading-models',
    }));
  }, []);

  // Start state synchronization phase
  const startStateSyncing = useCallback(() => {
    phaseStartTimeRef.current = Date.now();
    setLoadingState(prev => ({
      ...prev,
      phase: 'syncing-state',
    }));
  }, []);

  // Mark as ready
  const markReady = useCallback(() => {
    const loadTime = Date.now() - phaseStartTimeRef.current;
    console.log(`Loading completed in ${loadTime}ms`);
    
    setLoadingState({
      isLoading: false,
      phase: 'ready',
      error: null,
    });

    // Clear any pending timeouts
    if (initTimeoutRef.current) {
      clearTimeout(initTimeoutRef.current);
    }
  }, []);

  // Handle errors
  const setError = useCallback((error: string) => {
    setLoadingState(prev => ({
      ...prev,
      error,
      isLoading: false,
    }));
  }, []);

  // Auto-timeout for stuck loading states
  useEffect(() => {
    if (loadingState.phase === 'idle' || loadingState.phase === 'ready') {
      return;
    }

    // Set a timeout for each phase
    const timeout = loadingState.phase === 'loading-models' ? 10000 : 5000;
    
    initTimeoutRef.current = setTimeout(() => {
      console.warn(`Loading phase '${loadingState.phase}' timed out after ${timeout}ms`);
      setError(`Loading timed out during ${loadingState.phase} phase`);
    }, timeout);

    return () => {
      if (initTimeoutRef.current) {
        clearTimeout(initTimeoutRef.current);
      }
    };
  }, [loadingState.phase, setError]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (initTimeoutRef.current) {
        clearTimeout(initTimeoutRef.current);
      }
    };
  }, []);

  // Reset loading state
  const reset = useCallback(() => {
    if (initTimeoutRef.current) {
      clearTimeout(initTimeoutRef.current);
    }
    
    setLoadingState({
      isLoading: true,
      phase: 'idle',
      error: null,
    });
  }, []);

  // Check if a specific phase is safe to proceed
  const canProceedFromPhase = useCallback((phase: LoadingState['phase']) => {
    if (loadingState.error) return false;
    
    const phaseOrder: LoadingState['phase'][] = [
      'idle',
      'initializing', 
      'loading-models',
      'syncing-state',
      'ready'
    ];
    
    const currentIndex = phaseOrder.indexOf(loadingState.phase);
    const targetIndex = phaseOrder.indexOf(phase);
    
    return currentIndex >= targetIndex;
  }, [loadingState]);

  return {
    // Current state
    loadingState,
    isLoading: loadingState.isLoading,
    currentPhase: loadingState.phase,
    error: loadingState.error,
    isReady: loadingState.phase === 'ready' && !loadingState.error,
    
    // Phase control
    startInitialization,
    startModelLoading,
    startStateSyncing,
    markReady,
    setError,
    reset,
    
    // Utilities
    canProceedFromPhase,
    
    // Debug info
    getDebugInfo: () => ({
      ...loadingState,
      phaseStartTime: phaseStartTimeRef.current,
      totalLoadTime: loadingState.phase === 'ready' 
        ? Date.now() - phaseStartTimeRef.current 
        : null,
    }),
  };
}