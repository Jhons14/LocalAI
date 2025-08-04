import { memo, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
}

export interface ToastProps {
  toast: Toast;
  onClose: (id: string) => void;
}

const ToastIcon = memo(function ToastIcon({ type }: { type: ToastType }) {
  const iconProps = { size: 20 };
  
  switch (type) {
    case 'success':
      return <CheckCircle {...iconProps} className="text-green-500" />;
    case 'error':
      return <AlertCircle {...iconProps} className="text-red-500" />;
    case 'warning':
      return <AlertTriangle {...iconProps} className="text-orange-500" />;
    case 'info':
    default:
      return <Info {...iconProps} className="text-blue-500" />;
  }
});

export const ToastComponent = memo(function ToastComponent({ toast, onClose }: ToastProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (!toast.persistent && toast.duration !== 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(toast.id), 300);
      }, toast.duration || 5000);

      return () => clearTimeout(timer);
    }
  }, [toast.id, toast.duration, toast.persistent, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onClose(toast.id), 300);
  };

  const getToastStyles = () => {
    const baseStyles = "bg-white border-l-4 shadow-lg rounded-lg p-4 max-w-sm w-full";
    
    switch (toast.type) {
      case 'success':
        return `${baseStyles} border-green-500`;
      case 'error':
        return `${baseStyles} border-red-500`;
      case 'warning':
        return `${baseStyles} border-orange-500`;
      case 'info':
      default:
        return `${baseStyles} border-blue-500`;
    }
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 100, scale: 0.8 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 100, scale: 0.8 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className={getToastStyles()}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 mr-3">
              <ToastIcon type={toast.type} />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-gray-900 mb-1">
                {toast.title}
              </h4>
              {toast.message && (
                <p className="text-sm text-gray-600">{toast.message}</p>
              )}
            </div>
            <button
              onClick={handleClose}
              className="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600 transition-colors"
              aria-label="Close notification"
            >
              <X size={16} />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
});

export const ToastContainer = memo(function ToastContainer({ 
  toasts, 
  onClose 
}: { 
  toasts: Toast[]; 
  onClose: (id: string) => void; 
}) {
  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastComponent key={toast.id} toast={toast} onClose={onClose} />
        ))}
      </AnimatePresence>
    </div>
  );
});