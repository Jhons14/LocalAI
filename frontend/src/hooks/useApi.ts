import { useRef, useCallback } from 'react';
import { apiLogger } from '@/utils/logger';
import { captureApiError, captureNetworkError } from '@/utils/errorMonitoring';

interface ApiError {
  status: number;
  message: string;
}

interface StreamResponse {
  reader: ReadableStreamDefaultReader<Uint8Array>;
  response: Response;
}

export function useApi() {
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const controllerRef = useRef<AbortController | null>(null);

  const abortPreviousRequest = useCallback(() => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    return controller;
  }, []);

  const handleApiError = useCallback(
    (status: number, endpoint: string, statusText?: string): string => {
      const errorMessage = (() => {
        switch (status) {
          case 503:
            return 'Service is not available, please try again later';
          case 400:
            return 'Invalid request';
          case 401:
            return 'Unauthorized access';
          case 403:
            return 'Forbidden access';
          case 404:
            return 'Resource not found';
          case 500:
            return 'Internal server error';
          default:
            return 'An unexpected error occurred';
        }
      })();

      // Log and capture the error
      apiLogger.error(
        `API Error: ${status} ${statusText || ''} - ${endpoint}`,
        'API',
        { status, statusText, endpoint }
      );
      captureApiError(endpoint, status, statusText || 'Unknown', null);

      return errorMessage;
    },
    []
  );

  const makeRequest = useCallback(
    async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
      try {
        const response = await fetch(`${BACKEND_URL}${endpoint}`, {
          headers: {
            'Content-Type': 'application/json',
            ...options.headers,
          },
          ...options,
        });

        if (!response.ok) {
          const errorMessage = handleApiError(
            response.status,
            endpoint,
            response.statusText
          );
          throw new ApiError(response.status, errorMessage);
        }

        // Log successful request
        apiLogger.debug(`API Request successful: ${endpoint}`, 'API', {
          status: response.status,
        });

        return response;
      } catch (error) {
        if (error instanceof ApiError) {
          throw error;
        }

        // Capture network errors
        const networkError = error as Error;
        apiLogger.error(
          `Network error for ${endpoint}: ${networkError.message}`,
          'API'
        );
        captureNetworkError(`${BACKEND_URL}${endpoint}`, networkError);

        throw new ApiError(0, 'Network error occurred');
      }
    },
    [BACKEND_URL, handleApiError]
  );

  const streamRequest = useCallback(
    async (endpoint: string, data: object): Promise<StreamResponse> => {
      const controller = abortPreviousRequest();

      const response = await makeRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
        signal: controller.signal,
      });

      const reader = response.body?.getReader();
      if (!reader) {
        throw new ApiError(0, 'No reader available for streaming');
      }

      return { reader, response };
    },
    [makeRequest, abortPreviousRequest]
  );

  const postRequest = useCallback(
    async <T>(endpoint: string, data: object): Promise<T> => {
      const response = await makeRequest(endpoint, {
        method: 'POST',
        body: JSON.stringify(data),
      });

      return response.json();
    },
    [makeRequest]
  );

  const getRequest = useCallback(
    async <T>(endpoint: string): Promise<T> => {
      const response = await makeRequest(endpoint, {
        method: 'GET',
      });

      return response.json();
    },
    [makeRequest]
  );

  return {
    streamRequest,
    postRequest,
    getRequest,
    abortPreviousRequest,
    handleApiError,
  };
}

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}
