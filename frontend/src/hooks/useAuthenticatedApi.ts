/**
 * Hook for making authenticated API requests
 */

import { useAuth } from '../context/AuthContext';
import { useCallback } from 'react';

export function useAuthenticatedApi() {
  const { user, logout, refreshToken } = useAuth();

  const makeAuthenticatedRequest = useCallback(async (
    url: string,
    options: RequestInit = {}
  ): Promise<Response> => {
    // Get current access token from localStorage
    const accessToken = localStorage.getItem('auth_access_token');
    
    if (!accessToken) {
      throw new Error('No access token available');
    }

    // Prepare headers with auth token
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`,
    };

    // Make the request
    let response = await fetch(url, {
      ...options,
      headers,
    });

    // If we get a 401 (unauthorized), try to refresh the token
    if (response.status === 401) {
      const refreshSuccess = await refreshToken();
      
      if (refreshSuccess) {
        // Get the new token and retry the request
        const newAccessToken = localStorage.getItem('auth_access_token');
        const newHeaders = {
          ...headers,
          'Authorization': `Bearer ${newAccessToken}`,
        };

        response = await fetch(url, {
          ...options,
          headers: newHeaders,
        });
      } else {
        // Refresh failed, logout the user
        logout();
        throw new Error('Authentication failed');
      }
    }

    return response;
  }, [refreshToken, logout]);

  return {
    makeAuthenticatedRequest,
    isAuthenticated: !!user,
    user,
  };
}