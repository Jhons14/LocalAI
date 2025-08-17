import { useCallback } from 'react';
import { useApi } from './useApi';
import type {
  SendMessageParams,
  ConfigureModelParams,
  AddToolToModelParams,
} from '@/types/chat';

export function useChatApi() {
  const { streamRequest, postRequest, getRequest } = useApi();

  const sendChatMessage = useCallback(
    async (
      params: SendMessageParams,
      onChunk: (chunk: string) => void,
      onError: (error: string) => void,
      onComplete: () => void
    ) => {
      try {
        console.log('Sending chat message:', params.api_key);

        const { reader } = await streamRequest('/chat', {
          prompt: params.content,
          thread_id: params.thread_id,
          model: params.model,
          provider: params.provider,
          api_key: params.api_key,
          toolkits: params.toolkits,
          enable_memory: params.enable_memory,
        });

        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          onChunk(chunk);
        }

        onComplete();
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : 'Unknown error occurred';
        onError(errorMessage);
      }
    },
    [streamRequest]
  );

  const getOllamaModels = useCallback(async (): Promise<string[]> => {
    return getRequest('/models?provider=ollama');
  }, [postRequest]);

  return {
    sendChatMessage,
    getOllamaModels,
  };
}
