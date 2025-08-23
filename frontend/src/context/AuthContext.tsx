/**
 * Authentication context for managing auth state across the application
 */

import React, { createContext, useContext, useReducer, useEffect, type ReactNode } from 'react';
import type { AuthContextType, AuthState, User } from '../types/auth';
import { loginUser, logoutUser, refreshAccessToken } from '../services/authApi';

// Auth state actions
type AuthAction =
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; user: User; accessToken: string; refreshToken: string }
  | { type: 'LOGIN_FAILURE' }
  | { type: 'LOGOUT' }
  | { type: 'REFRESH_TOKEN_SUCCESS'; accessToken: string }
  | { type: 'SET_LOADING'; isLoading: boolean };

// Initial auth state
const initialState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  isAuthenticated: false,
  isLoading: false,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN_START':
      return { ...state, isLoading: true };
    
    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.user,
        accessToken: action.accessToken,
        refreshToken: action.refreshToken,
        isAuthenticated: true,
        isLoading: false,
      };
    
    case 'LOGIN_FAILURE':
      return { ...state, isLoading: false };
    
    case 'LOGOUT':
      return { ...initialState };
    
    case 'REFRESH_TOKEN_SUCCESS':
      return { ...state, accessToken: action.accessToken };
    
    case 'SET_LOADING':
      return { ...state, isLoading: action.isLoading };
    
    default:
      return state;
  }
}

// Create auth context
const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Storage keys
const STORAGE_KEYS = {
  ACCESS_TOKEN: 'auth_access_token',
  REFRESH_TOKEN: 'auth_refresh_token',
  USER: 'auth_user',
} as const;

// Auth provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth state from localStorage on mount
  useEffect(() => {
    const initializeAuth = () => {
      try {
        const storedAccessToken = localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
        const storedRefreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);

        if (storedAccessToken && storedRefreshToken && storedUser) {
          const user = JSON.parse(storedUser);
          dispatch({
            type: 'LOGIN_SUCCESS',
            user,
            accessToken: storedAccessToken,
            refreshToken: storedRefreshToken,
          });
        }
      } catch (error) {
        console.error('Error initializing auth from storage:', error);
        // Clear corrupted data
        clearAuthStorage();
      }
    };

    initializeAuth();
  }, []);

  // Helper function to save auth data to localStorage
  const saveAuthToStorage = (user: User, accessToken: string, refreshToken: string) => {
    try {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken);
      localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
      localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
    } catch (error) {
      console.error('Error saving auth to storage:', error);
    }
  };

  // Helper function to clear auth data from localStorage
  const clearAuthStorage = () => {
    try {
      localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
      localStorage.removeItem(STORAGE_KEYS.USER);
    } catch (error) {
      console.error('Error clearing auth storage:', error);
    }
  };

  // Login function
  const login = async (email: string, password: string): Promise<boolean> => {
    try {
      dispatch({ type: 'LOGIN_START' });

      const response = await loginUser({ email, password });
      
      const user: User = {
        user_id: response.user_id,
        email: response.email,
        username: response.username,
        is_admin: response.is_admin,
      };

      // Save to localStorage
      saveAuthToStorage(user, response.access_token, response.refresh_token);

      // Update state
      dispatch({
        type: 'LOGIN_SUCCESS',
        user,
        accessToken: response.access_token,
        refreshToken: response.refresh_token,
      });

      return true;
    } catch (error) {
      console.error('Login error:', error);
      dispatch({ type: 'LOGIN_FAILURE' });
      return false;
    }
  };

  // Logout function
  const logout = async () => {
    try {
      // Call logout API if we have an access token
      if (state.accessToken) {
        await logoutUser(state.accessToken);
      }
    } catch (error) {
      console.error('Logout API error:', error);
      // Continue with logout even if API call fails
    } finally {
      // Clear storage and state
      clearAuthStorage();
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    try {
      if (!state.refreshToken) {
        return false;
      }

      const response = await refreshAccessToken({ refresh_token: state.refreshToken });
      
      // Update stored access token
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, response.access_token);
      
      // Update state
      dispatch({
        type: 'REFRESH_TOKEN_SUCCESS',
        accessToken: response.access_token,
      });

      return true;
    } catch (error) {
      console.error('Token refresh error:', error);
      // If refresh fails, logout the user
      logout();
      return false;
    }
  };

  // Context value
  const contextValue: AuthContextType = {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    login,
    logout,
    refreshToken,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}