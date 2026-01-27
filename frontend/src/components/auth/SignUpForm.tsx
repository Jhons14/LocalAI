/**
 * Sign up form component for modal use
 */

import React, { useState } from 'react';
import { registerUser } from '../../services/authApi';
import { useAuth } from '../../context/AuthContext';

interface SignUpFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export function SignUpForm({ onSuccess, onSwitchToLogin }: SignUpFormProps) {
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) setError(null);
  };

  const validateForm = (): string | null => {
    if (!formData.username || !formData.email || !formData.password) {
      return 'All fields are required';
    }

    if (formData.username.length < 3) {
      return 'Username must be at least 3 characters long';
    }

    if (!formData.email.includes('@')) {
      return 'Please enter a valid email address';
    }

    if (formData.password.length < 8) {
      return 'Password must be at least 8 characters long';
    }

    if (formData.password !== formData.confirmPassword) {
      return 'Passwords do not match';
    }

    // Basic password strength check
    if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(formData.password)) {
      return 'Password must contain at least one uppercase letter, one lowercase letter, and one number';
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate form
    const validationError = validateForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);

    try {
      // Register user
      await registerUser({
        username: formData.username,
        email: formData.email,
        password: formData.password,
      });

      // Auto-login after successful registration
      const loginSuccess = await login(formData.email, formData.password);
      
      if (loginSuccess) {
        onSuccess?.();
      } else {
        setError('Account created successfully, but auto-login failed. Please try logging in manually.');
      }
    } catch (error) {
      if (error.message.includes('already exists')) {
        setError('An account with this email or username already exists');
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="bg-red-50 border border-red-300 text-red-800 p-3 rounded mb-4 text-sm">
            {error}
          </div>
        )}

        <div className="mb-4">
          <label htmlFor="signup-username" className="block mb-2 font-medium text-black">
            Username
          </label>
          <input
            type="text"
            id="signup-username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            className="w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Choose a username"
            required
            disabled={isLoading}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="signup-email" className="block mb-2 font-medium text-black">
            Email
          </label>
          <input
            type="email"
            id="signup-email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className="w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Enter your email"
            required
            disabled={isLoading}
          />
        </div>

        <div className="mb-4">
          <label htmlFor="signup-password" className="block mb-2 font-medium text-black">
            Password
          </label>
          <input
            type="password"
            id="signup-password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className="w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Create a password"
            required
            disabled={isLoading}
          />
          <div className="text-xs text-black mt-1">
            Must be at least 8 characters with uppercase, lowercase, and number
          </div>
        </div>

        <div className="mb-4">
          <label htmlFor="signup-confirm-password" className="block mb-2 font-medium text-black">
            Confirm Password
          </label>
          <input
            type="password"
            id="signup-confirm-password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className="w-full p-3 border border-gray-300 rounded text-base text-black transition-colors duration-200 box-border focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:bg-gray-100 disabled:cursor-not-allowed"
            placeholder="Confirm your password"
            required
            disabled={isLoading}
          />
        </div>

        <div className="mt-6 mb-4">
          <button
            type="submit"
            className="w-full p-3 border-none rounded text-base font-medium cursor-pointer transition-colors duration-200 bg-green-600 text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-60"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </div>

        <div className="border-t border-gray-200 pt-4 text-center">
          <p className="m-0 text-black text-sm">
            Already have an account?{' '}
            <button
              type="button"
              className="bg-transparent border-none text-blue-600 cursor-pointer underline text-inherit p-0 hover:text-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
              onClick={onSwitchToLogin}
              disabled={isLoading}
            >
              Sign in
            </button>
          </p>
        </div>
      </form>
    </div>
  );
}