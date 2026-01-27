import { useCallback } from 'react';
import { useApi } from './useApi';
import type { SendMessageParams } from '@/types/chat';

export function useChatApi() {
  const { streamRequest, streamFormDataRequest, postRequest, getRequest, abortPreviousRequest } = useApi();

  const sendChatMessage = useCallback(
    async (
      params: SendMessageParams,
      onChunk: (chunk: string) => void,
      onError: (error: string) => void,
      onComplete: () => void
    ) => {
      try {
        let reader: ReadableStreamDefaultReader<Uint8Array>;

        // If there's a document, use multipart form data upload
        if (params.document) {
          const formData = new FormData();
          formData.append('thread_id', params.thread_id);
          formData.append('prompt', params.content);
          formData.append('model', params.model);
          formData.append('provider', params.provider);
          formData.append('toolkits', JSON.stringify(params.toolkits));
          formData.append('enable_memory', String(params.enable_memory ?? true));
          formData.append('document', params.document);

          if (params.api_key) {
            formData.append('api_key', params.api_key);
          }

          const response = await streamFormDataRequest('/chat-upload', formData);
          reader = response.reader;
        } else {
          // No document, use JSON request
          const requestData: any = {
            prompt: params.content,
            thread_id: params.thread_id,
            model: params.model,
            provider: params.provider,
            toolkits: params.toolkits,
            enable_memory: params.enable_memory,
          };

          if (params.api_key) {
            requestData.api_key = params.api_key;
          }

          const response = await streamRequest('/chat', requestData);
          reader = response.reader;
        }

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          onChunk(chunk);
        }

        onComplete();
      } catch (error) {
        // Handle abort errors gracefully
        if (error instanceof Error && error.name === 'AbortError') {
          onError('Request was cancelled');
          return;
        }

        const errorMessage =
          error instanceof Error ? error.message : 'Unknown error occurred';
        onError(errorMessage);
      }
    },
    [streamRequest, streamFormDataRequest]
  );

  const getOllamaModels = useCallback(async (): Promise<string[]> => {
    return getRequest('/models?provider=ollama');
  }, [getRequest]);

  const cancelCurrentRequest = useCallback(() => {
    abortPreviousRequest();
  }, [abortPreviousRequest]);

  return {
    sendChatMessage,
    getOllamaModels,
    cancelCurrentRequest,
  };
}
