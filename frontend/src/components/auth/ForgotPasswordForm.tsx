/**
 * Forgot password form component for modal use
 */

import React, { useState } from 'react';
import { forgotPassword } from '../../services/authApi';
import { useToast } from '../../hooks/useToast';

interface ForgotPasswordFormProps {
  onSuccess?: () => void;
  onClose?: () => void;
  onCloseAll?: () => void;
  initialEmail?: string;
}

export function ForgotPasswordForm({
  onSuccess,
  onClose,
  onCloseAll,
  initialEmail = '',
}: ForgotPasswordFormProps) {
  const [email, setEmail] = useState(initialEmail);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { success: showSuccessToast } = useToast();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!email) {
      setError('Email address is required');
      return;
    }

    if (!email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setIsLoading(true);

    try {
      await forgotPassword(email);
      showSuccessToast(
        'Reset link sent',
        'If your email is registered, you will receive a password reset link shortly.',
        { duration: 6000 }
      );
      onCloseAll?.();
    } catch (error) {
      console.error('Forgot password error:', error);
      // Always show success message for security (prevent email enumeration)
      showSuccessToast(
        'Reset link sent',
        'If your email is registered, you will receive a password reset link shortly.',
        { duration: 6000 }
      );
      onCloseAll?.();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='w-full'>
      <form onSubmit={handleSubmit}>
        {error && (
          <div className='bg-red-50 border border-red-300 text-red-800 p-3 rounded mb-4 text-sm'>
            {error}
          </div>
        )}

        <div className='mb-4'>
          <p className='text-black text-sm mb-4'>
            Enter your email address and we'll send you a link to reset your
            password.
          </p>
        </div>

        <div className='mb-4'>
          <label
            htmlFor='forgot-email'
            className='block mb-2 font-medium text-black'
          >
            Email
          </label>
          <input
            type='email'
            id='forgot-email'
            name='email'
            value={email}
            onChange={handleInputChange}
            className='w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed'
            placeholder='Enter your email address'
            required
            disabled={isLoading}
            autoFocus
          />
        </div>

        <div className='mt-6 mb-4'>
          <button
            type='submit'
            className='w-full p-3 border-none rounded text-base font-medium cursor-pointer transition-colors duration-200 bg-blue-600 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60'
            disabled={isLoading}
          >
            {isLoading ? 'Sending...' : 'Send Reset Link'}
          </button>
        </div>

        <div className='border-t border-gray-200 pt-4 text-center'>
          <p className='m-0 text-black text-sm'>
            Remember your password?{' '}
            <button
              type='button'
              className='bg-transparent border-none text-blue-600 cursor-pointer underline p-0 hover:text-blue-700 disabled:opacity-60 disabled:cursor-not-allowed'
              onClick={onClose}
              disabled={isLoading}
            >
              Back to sign in
            </button>
          </p>
        </div>
      </form>
    </div>
  );
}
