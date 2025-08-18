import { createContext, useState, useCallback } from 'react';
import { v4 as uuid } from 'uuid';
import type { Toast, ToastType } from '@/components/ui/Toast';

export interface ToastContextValue {
  toasts: Toast[];
  addToast: (
    type: ToastType,
    title: string,
    message?: string,
    options?: {
      duration?: number;
      persistent?: boolean;
    }
  ) => string;
  removeToast: (id: string) => void;
  clearAllToasts: () => void;
  success: (title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => string;
  error: (title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => string;
  warning: (title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => string;
  info: (title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => string;
}

export const ToastContext = createContext<ToastContextValue | undefined>(
  undefined
);

export function ToastProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((
    type: ToastType,
    title: string,
    message?: string,
    options?: {
      duration?: number;
      persistent?: boolean;
    }
  ) => {
    const id = uuid();
    const newToast: Toast = {
      id,
      type,
      title,
      message,
      duration: options?.duration,
      persistent: options?.persistent,
    };

    setToasts(prev => [...prev, newToast]);
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  }, []);

  const clearAllToasts = useCallback(() => {
    setToasts([]);
  }, []);

  // Convenience methods
  const success = useCallback((title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => {
    return addToast('success', title, message, options);
  }, [addToast]);

  const error = useCallback((title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => {
    return addToast('error', title, message, options);
  }, [addToast]);

  const warning = useCallback((title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => {
    return addToast('warning', title, message, options);
  }, [addToast]);

  const info = useCallback((title: string, message?: string, options?: { duration?: number; persistent?: boolean }) => {
    return addToast('info', title, message, options);
  }, [addToast]);

  return (
    <ToastContext.Provider
      value={{
        toasts,
        addToast,
        removeToast,
        clearAllToasts,
        success,
        error,
        warning,
        info,
      }}
    >
      {children}
    </ToastContext.Provider>
  );
}