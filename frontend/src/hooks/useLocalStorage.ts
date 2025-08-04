import { useState, useEffect, useCallback } from 'react';
import { safeLocalStorage } from '@/utils/common';

export interface UseLocalStorageOptions<T> {
  serializer?: {
    read: (value: string) => T;
    write: (value: T) => string;
  };
  syncAcrossTabs?: boolean;
}

export function useLocalStorage<T>(
  key: string,
  initialValue: T,
  options?: UseLocalStorageOptions<T>
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  const serializer = options?.serializer || {
    read: (v: string) => {
      try {
        return JSON.parse(v);
      } catch {
        return v as T;
      }
    },
    write: (v: T) => JSON.stringify(v),
  };

  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? serializer.read(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        
        if (valueToStore === undefined) {
          localStorage.removeItem(key);
        } else {
          localStorage.setItem(key, serializer.write(valueToStore));
        }
      } catch (error) {
        console.error(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue, serializer]
  );

  const removeValue = useCallback(() => {
    try {
      localStorage.removeItem(key);
      setStoredValue(initialValue);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // Sync across tabs
  useEffect(() => {
    if (!options?.syncAcrossTabs) return;

    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== null) {
        try {
          setStoredValue(serializer.read(e.newValue));
        } catch {
          setStoredValue(initialValue);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [key, initialValue, serializer, options?.syncAcrossTabs]);

  return [storedValue, setValue, removeValue];
}