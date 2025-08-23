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
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {title && (
          <div className="modal-header">
            <h2 className="modal-title">{title}</h2>
            <button 
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close modal"
            >
              ×
            </button>
          </div>
        )}
        <div className="modal-body">
          {children}
        </div>
      </div>

      <style jsx>{`
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
          padding: 1rem;
        }

        .modal-content {
          background: white;
          border-radius: 8px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
          width: 100%;
          max-width: 500px;
          max-height: 90vh;
          overflow-y: auto;
          position: relative;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1.5rem 1.5rem 0;
          margin-bottom: 1rem;
        }

        .modal-title {
          color: #333;
          font-size: 1.5rem;
          font-weight: 600;
          margin: 0;
        }

        .modal-close-btn {
          background: none;
          border: none;
          font-size: 2rem;
          color: #666;
          cursor: pointer;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          justify-content: center;
          align-items: center;
          border-radius: 4px;
          transition: all 0.2s;
        }

        .modal-close-btn:hover {
          background-color: #f5f5f5;
          color: #333;
        }

        .modal-body {
          padding: 0 1.5rem 1.5rem;
        }

        @media (max-width: 768px) {
          .modal-overlay {
            padding: 0.5rem;
          }
          
          .modal-content {
            max-width: none;
            margin: 0;
          }
          
          .modal-header {
            padding: 1rem 1rem 0;
          }
          
          .modal-body {
            padding: 0 1rem 1rem;
          }
        }
      `}</style>
    </div>
  );
}