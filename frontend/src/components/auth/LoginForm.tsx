/**
 * Login form component for modal use
 */

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToSignUp?: () => void;
  onSwitchToForgotPassword?: (email?: string) => void;
}

export function LoginForm({
  onSuccess,
  onSwitchToSignUp,
  onSwitchToForgotPassword,
}: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Basic validation
    if (!formData.email || !formData.password) {
      setError('Email and password are required');
      return;
    }

    // Attempt login
    const success = await login(formData.email, formData.password);

    if (success) {
      onSuccess?.();
    } else {
      setError('Invalid email or password. Please try again.');
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
          <label htmlFor='email' className='block mb-2 font-medium text-black'>
            Email
          </label>
          <input
            type='email'
            id='email'
            name='email'
            value={formData.email}
            onChange={handleInputChange}
            className='w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed'
            placeholder='Enter your email'
            required
            disabled={isLoading}
          />
        </div>

        <div className='mb-4'>
          <label
            htmlFor='password'
            className='block mb-2 font-medium text-black'
          >
            Password
          </label>
          <input
            type='password'
            id='password'
            name='password'
            value={formData.password}
            onChange={handleInputChange}
            className='w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed'
            placeholder='Enter your password'
            required
            disabled={isLoading}
          />
        </div>

        <div className='mb-4 text-right'>
          <button
            type='button'
            className='bg-transparent border-none text-blue-600 cursor-pointer underline text-sm p-0 hover:text-blue-700 disabled:opacity-60 disabled:cursor-not-allowed'
            onClick={() => onSwitchToForgotPassword?.(formData.email)}
            disabled={isLoading}
          >
            Forgot password?
          </button>
        </div>

        <div className='mt-6 mb-4'>
          <button
            type='submit'
            className='w-full p-3 border-none rounded text-base font-medium cursor-pointer transition-colors duration-200 bg-blue-600 text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60'
            disabled={isLoading}
          >
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>

        <div className='border-t border-gray-200 pt-4 text-center'>
          <p className='m-0 text-black text-sm'>
            Don't have an account?{' '}
            <button
              type='button'
              className='bg-transparent border-none text-blue-600 cursor-pointer underline p-0 hover:text-blue-700 disabled:opacity-60 disabled:cursor-not-allowed'
              onClick={onSwitchToSignUp}
              disabled={isLoading}
            >
              Create account
            </button>
          </p>
        </div>
      </form>
    </div>
  );
}
