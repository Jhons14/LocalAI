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
    <div className="signup-form">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="signup-username" className="form-label">
            Username
          </label>
          <input
            type="text"
            id="signup-username"
            name="username"
            value={formData.username}
            onChange={handleInputChange}
            className="form-input"
            placeholder="Choose a username"
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="signup-email" className="form-label">
            Email
          </label>
          <input
            type="email"
            id="signup-email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className="form-input"
            placeholder="Enter your email"
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="signup-password" className="form-label">
            Password
          </label>
          <input
            type="password"
            id="signup-password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className="form-input"
            placeholder="Create a password"
            required
            disabled={isLoading}
          />
          <div className="password-help">
            Must be at least 8 characters with uppercase, lowercase, and number
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="signup-confirm-password" className="form-label">
            Confirm Password
          </label>
          <input
            type="password"
            id="signup-confirm-password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleInputChange}
            className="form-input"
            placeholder="Confirm your password"
            required
            disabled={isLoading}
          />
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn btn-primary btn-full"
            disabled={isLoading}
          >
            {isLoading ? 'Creating Account...' : 'Create Account'}
          </button>
        </div>

        <div className="form-footer">
          <p className="login-prompt">
            Already have an account?{' '}
            <button
              type="button"
              className="link-button"
              onClick={onSwitchToLogin}
              disabled={isLoading}
            >
              Sign in
            </button>
          </p>
        </div>
      </form>

      <style jsx>{`
        .signup-form {
          width: 100%;
        }

        .error-message {
          background: #fee;
          border: 1px solid #fcc;
          color: #c33;
          padding: 0.75rem;
          border-radius: 4px;
          margin-bottom: 1rem;
          font-size: 0.875rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
          color: #555;
        }

        .form-input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 1rem;
          transition: border-color 0.2s;
          box-sizing: border-box;
        }

        .form-input:focus {
          outline: none;
          border-color: #007bff;
          box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
        }

        .form-input:disabled {
          background-color: #f5f5f5;
          cursor: not-allowed;
        }

        .password-help {
          font-size: 0.75rem;
          color: #666;
          margin-top: 0.25rem;
        }

        .form-actions {
          margin-top: 1.5rem;
          margin-bottom: 1rem;
        }

        .btn {
          padding: 0.75rem 1rem;
          border: none;
          border-radius: 4px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background-color 0.2s;
        }

        .btn-full {
          width: 100%;
        }

        .btn:disabled {
          cursor: not-allowed;
          opacity: 0.6;
        }

        .btn-primary {
          background-color: #28a745;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #218838;
        }

        .form-footer {
          border-top: 1px solid #eee;
          padding-top: 1rem;
          text-align: center;
        }

        .login-prompt {
          margin: 0;
          color: #666;
          font-size: 0.9rem;
        }

        .link-button {
          background: none;
          border: none;
          color: #007bff;
          cursor: pointer;
          text-decoration: underline;
          font-size: inherit;
          padding: 0;
        }

        .link-button:hover:not(:disabled) {
          color: #0056b3;
        }

        .link-button:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}