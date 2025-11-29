/**
 * Authentication status component with modal forms
 */

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Modal } from '../ui/Modal';
import { LoginForm } from './LoginForm';
import { SignUpForm } from './SignUpForm';
import { ForgotPasswordForm } from './ForgotPasswordForm';

type ModalType = 'login' | 'signup' | 'forgot-password' | null;

export function AuthStatus() {
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const [activeModal, setActiveModal] = useState<ModalType>(null);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');

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

  const switchToForgotPassword = (email?: string) => {
    if (email) {
      setForgotPasswordEmail(email);
    }
    setActiveModal('forgot-password');
  };

  return (
    <>
      <div className='px-4'>
        {isAuthenticated && user ? (
          <div className='flex justify-between flex-wrap gap-3 md:flex-row flex-col md:items-center items-start'>
            <div className='flex flex-col gap-1'>
              <span className='font-semibold  text-sm'>
                Welcome, {user.username}!
              </span>
              <span className='text-sm '>{user.email}</span>
              {user.is_admin && (
                <span className='bg-red-600 text-white px-2 py-0.5 rounded-full text-xs font-medium self-start'>
                  Admin
                </span>
              )}
            </div>
            <button
              onClick={handleLogout}
              className='bg-red-600 text-white border-none px-4 py-2 rounded text-sm font-medium cursor-pointer transition-colors duration-200 hover:bg-red-700 disabled:opacity-60 disabled:cursor-not-allowed'
              disabled={isLoading}
            >
              {isLoading ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        ) : (
          <div className='flex justify-between gap-3 md:flex-row flex-col md:items-center items-start'>
            <span className=' text-sm'>Not signed in</span>
            <button
              onClick={() => openModal('login')}
              className='bg-blue-600 text-white border-none px-4 py-2 rounded text-sm font-medium cursor-pointer transition-colors duration-200 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed'
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
        title='Sign In'
      >
        <LoginForm
          onSuccess={handleLoginSuccess}
          onSwitchToSignUp={switchToSignUp}
          onSwitchToForgotPassword={switchToForgotPassword}
        />
      </Modal>

      {/* Sign Up Modal */}
      <Modal
        isOpen={activeModal === 'signup'}
        onClose={closeModal}
        title='Create Account'
      >
        <SignUpForm
          onSuccess={handleSignUpSuccess}
          onSwitchToLogin={switchToLogin}
        />
      </Modal>

      {/* Forgot Password Modal */}
      <Modal
        isOpen={activeModal === 'forgot-password'}
        onClose={closeModal}
        title='Reset Password'
      >
        <ForgotPasswordForm
          onSuccess={closeModal}
          onClose={switchToLogin}
          onCloseAll={closeModal}
          initialEmail={forgotPasswordEmail}
        />
      </Modal>
    </>
  );
}
