import { useCallback } from 'react';
import { useApi } from './useApi';
import type {
  SendMessageParams,
  ConfigureModelParams,
  AddToolToModelParams,
} from '@/types/chat';

export function useChatApi() {
  const { streamRequest, postRequest, getRequest, abortPreviousRequest } = useApi();

  const sendChatMessage = useCallback(
    async (
      params: SendMessageParams,
      onChunk: (chunk: string) => void,
      onError: (error: string) => void,
      onComplete: () => void
    ) => {
      try {
        const requestData: any = {
          prompt: params.content,
          thread_id: params.thread_id,
          model: params.model,
          provider: params.provider,
          toolkits: params.toolkits,
          enable_memory: params.enable_memory,
        };
        
        // Only include document fields if they have values
        if (params.document_filename) {
          requestData.document_filename = params.document_filename;
        }
        if (params.document_content) {
          requestData.document_content = params.document_content;
        }
        if (params.api_key) {
          requestData.api_key = params.api_key;
        }
        
        const { reader } = await streamRequest('/chat', requestData);

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
    [streamRequest]
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
