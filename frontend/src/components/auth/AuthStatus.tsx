/**
 * Authentication status component with modal forms
 */

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Modal } from '../ui/Modal';
import { LoginForm } from './LoginForm';
import { SignUpForm } from './SignUpForm';

type ModalType = 'login' | 'signup' | null;

export function AuthStatus() {
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const [activeModal, setActiveModal] = useState<ModalType>(null);

  const handleLoginSuccess = () => {
    setActiveModal(null);
  };

  const handleSignUpSuccess = () => {
    setActiveModal(null);
  };

  const handleLogout = async () => {
    await logout();
  };

  const openModal = (modalType: ModalType) => {
    setActiveModal(modalType);
  };

  const closeModal = () => {
    setActiveModal(null);
  };

  const switchToSignUp = () => {
    setActiveModal('signup');
  };

  const switchToLogin = () => {
    setActiveModal('login');
  };

  return (
    <>
      <div className="auth-status">
        {isAuthenticated && user ? (
          <div className="auth-user-info">
            <div className="user-details">
              <span className="user-greeting">Welcome, {user.username}!</span>
              <span className="user-email">{user.email}</span>
              {user.is_admin && (
                <span className="admin-badge">Admin</span>
              )}
            </div>
            <button
              onClick={handleLogout}
              className="logout-btn"
              disabled={isLoading}
            >
              {isLoading ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        ) : (
          <div className="auth-login-prompt">
            <span className="login-text">Not signed in</span>
            <button
              onClick={() => openModal('login')}
              className="login-btn"
              disabled={isLoading}
            >
              Sign In
            </button>
          </div>
        )}
      </div>

      {/* Login Modal */}
      <Modal
        isOpen={activeModal === 'login'}
        onClose={closeModal}
        title="Sign In"
      >
        <LoginForm
          onSuccess={handleLoginSuccess}
          onSwitchToSignUp={switchToSignUp}
        />
      </Modal>

      {/* Sign Up Modal */}
      <Modal
        isOpen={activeModal === 'signup'}
        onClose={closeModal}
        title="Create Account"
      >
        <SignUpForm
          onSuccess={handleSignUpSuccess}
          onSwitchToLogin={switchToLogin}
        />
      </Modal>

      <style jsx>{`
        .auth-status {
          padding: 1rem;
          border-bottom: 1px solid #eee;
        }

        .auth-user-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 0.75rem;
        }

        .user-details {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .user-greeting {
          font-weight: 600;
          color: #333;
          font-size: 0.95rem;
        }

        .user-email {
          font-size: 0.85rem;
          color: #666;
        }

        .admin-badge {
          background: #dc3545;
          color: white;
          padding: 0.125rem 0.375rem;
          border-radius: 10px;
          font-size: 0.7rem;
          font-weight: 500;
          align-self: flex-start;
        }

        .logout-btn {
          background: #dc3545;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .logout-btn:hover:not(:disabled) {
          background: #c82333;
        }

        .logout-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .auth-login-prompt {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 0.75rem;
        }

        .login-text {
          color: #666;
          font-size: 0.9rem;
        }

        .login-btn {
          background: #007bff;
          color: white;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 4px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .login-btn:hover:not(:disabled) {
          background: #0056b3;
        }

        .login-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .auth-user-info {
            flex-direction: column;
            align-items: flex-start;
          }

          .auth-login-prompt {
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>
    </>
  );
}