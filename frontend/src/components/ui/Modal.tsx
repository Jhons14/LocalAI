/**
 * Modal component for overlaying content
 */

import React, { useEffect, type ReactNode } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
}

export function Modal({ isOpen, onClose, children, title }: ModalProps) {
  // Close modal on ESC key
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-center items-center z-[1000] p-4" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto relative md:p-0 p-2" onClick={(e) => e.stopPropagation()}>
        {title && (
          <div className="flex justify-between items-center px-6 pt-6 pb-0 mb-4">
            <h2 className="text-black text-2xl font-semibold m-0">{title}</h2>
            <button
              className="bg-transparent border-none text-2xl text-gray-600 cursor-pointer p-0 w-8 h-8 flex justify-center items-center rounded transition-all duration-200 hover:bg-gray-100 hover:text-black"
              onClick={onClose}
              aria-label='Close modal'
            >
              ×
            </button>
          </div>
        )}
        <div className="px-6 pb-6">{children}</div>
      </div>
    </div>
  );
}
