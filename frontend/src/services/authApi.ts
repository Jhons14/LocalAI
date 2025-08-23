/**
 * Authentication API service functions
 */

import type { 
  LoginRequest, 
  RegisterRequest, 
  AuthResponse, 
  RefreshTokenRequest, 
  RefreshTokenResponse,
  User 
} from '../types/auth';

const API_BASE_URL = import.meta.env.PUBLIC_BACKEND_URL || 'http://localhost:8003';

export class AuthApiError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = 'AuthApiError';
  }
}

/**
 * Login user with email and password
 */
export async function loginUser(credentials: LoginRequest): Promise<AuthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new AuthApiError(`Login failed: ${errorData}`, response.status);
    }

    const data: AuthResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }
    throw new AuthApiError(`Network error during login: ${error.message}`);
  }
}

/**
 * Register new user
 */
export async function registerUser(userData: RegisterRequest): Promise<AuthResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new AuthApiError(`Registration failed: ${errorData}`, response.status);
    }

    const data: AuthResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }
    throw new AuthApiError(`Network error during registration: ${error.message}`);
  }
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(refreshTokenData: RefreshTokenRequest): Promise<RefreshTokenResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(refreshTokenData),
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new AuthApiError(`Token refresh failed: ${errorData}`, response.status);
    }

    const data: RefreshTokenResponse = await response.json();
    return data;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }
    throw new AuthApiError(`Network error during token refresh: ${error.message}`);
  }
}

/**
 * Logout user (invalidate tokens)
 */
export async function logoutUser(accessToken: string): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Even if logout fails, we'll clear local tokens
      console.warn('Logout request failed, but clearing local tokens');
    }
  } catch (error) {
    // Even if network fails, we'll clear local tokens
    console.warn('Network error during logout, but clearing local tokens:', error.message);
  }
}

/**
 * Get current user info
 */
export async function getCurrentUser(accessToken: string): Promise<User> {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new AuthApiError(`Failed to get user info: ${errorData}`, response.status);
    }

    const data: User = await response.json();
    return data;
  } catch (error) {
    if (error instanceof AuthApiError) {
      throw error;
    }
    throw new AuthApiError(`Network error getting user info: ${error.message}`);
  }
}