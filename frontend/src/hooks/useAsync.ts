import { useCallback, useEffect, useRef, useState } from 'react';

export interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
}

export interface UseAsyncOptions {
  immediate?: boolean;
  onSuccess?: (data: any) => void;
  onError?: (error: Error) => void;
}

export function useAsync<T>(
  asyncFunction: () => Promise<T>,
  deps: React.DependencyList = [],
  options: UseAsyncOptions = {}
): AsyncState<T> & { execute: () => Promise<void>; reset: () => void } {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    loading: false,
  });

  const { immediate = true, onSuccess, onError } = options;
  const mountedRef = useRef(true);

  const execute = useCallback(async () => {
    setState({ data: null, error: null, loading: true });

    try {
      const result = await asyncFunction();
      
      if (mountedRef.current) {
        setState({ data: result, error: null, loading: false });
        onSuccess?.(result);
      }
    } catch (error) {
      if (mountedRef.current) {
        const err = error instanceof Error ? error : new Error(String(error));
        setState({ data: null, error: err, loading: false });
        onError?.(err);
      }
    }
  }, deps);

  const reset = useCallback(() => {
    setState({ data: null, error: null, loading: false });
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return { ...state, execute, reset };
}

export function useAsyncCallback<T extends any[], R>(
  asyncFunction: (...args: T) => Promise<R>,
  deps: React.DependencyList = []
): [(...args: T) => Promise<void>, AsyncState<R>] {
  const [state, setState] = useState<AsyncState<R>>({
    data: null,
    error: null,
    loading: false,
  });

  const mountedRef = useRef(true);

  const execute = useCallback(
    async (...args: T) => {
      setState({ data: null, error: null, loading: true });

      try {
        const result = await asyncFunction(...args);
        
        if (mountedRef.current) {
          setState({ data: result, error: null, loading: false });
        }
      } catch (error) {
        if (mountedRef.current) {
          const err = error instanceof Error ? error : new Error(String(error));
          setState({ data: null, error: err, loading: false });
        }
      }
    },
    deps
  );

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  return [execute, state];
}