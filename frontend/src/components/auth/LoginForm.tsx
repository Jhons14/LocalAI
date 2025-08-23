/**
 * Login form component for modal use
 */

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToSignUp?: () => void;
}

export function LoginForm({ onSuccess, onSwitchToSignUp }: LoginFormProps) {
  const { login, isLoading } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
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
    <div className="login-form">
      <form onSubmit={handleSubmit}>
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="email" className="form-label">
            Email
          </label>
          <input
            type="email"
            id="email"
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
          <label htmlFor="password" className="form-label">
            Password
          </label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleInputChange}
            className="form-input"
            placeholder="Enter your password"
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
            {isLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </div>

        <div className="form-footer">
          <p className="signup-prompt">
            Don't have an account?{' '}
            <button
              type="button"
              className="link-button"
              onClick={onSwitchToSignUp}
              disabled={isLoading}
            >
              Create account
            </button>
          </p>
        </div>
      </form>

      <style jsx>{`
        .login-form {
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
          background-color: #007bff;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background-color: #0056b3;
        }

        .form-footer {
          border-top: 1px solid #eee;
          padding-top: 1rem;
          text-align: center;
        }

        .signup-prompt {
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