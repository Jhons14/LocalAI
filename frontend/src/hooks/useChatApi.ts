import { useCallback } from 'react';
import { useApi } from './useApi';
import type { SendMessageParams, ConfigureModelParams, AddToolToModelParams } from '@/types/chat';

export function useChatApi() {
  const { streamRequest, postRequest, getRequest } = useApi();

  const sendChatMessage = useCallback(async (
    params: SendMessageParams,
    onChunk: (chunk: string) => void,
    onError: (error: string) => void,
    onComplete: () => void
  ) => {
    try {
      const { reader } = await streamRequest('/chat', {
        prompt: params.content,
        thread_id: params.thread_id,
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
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      onError(errorMessage);
    }
  }, [streamRequest]);

  const configureModel = useCallback(async (params: ConfigureModelParams & { apiKey?: string }) => {
    return postRequest('/configure', {
      
      thread_id: params.thread_id,
      model: params.model,
      provider: params.provider,
      apiKey: params.apiKey,
    });
  }, [postRequest]);

  const addToolsToModel = useCallback(async (params: AddToolToModelParams & { thread_id?: string }) => {
    return postRequest('/configure', {
    "thread_id": params.thread_id,
    "provider": "ollama",
    "model": "qwen3:1.7b",
    "toolkits": ["Gmail"],
    "enable_memory": true
});
  }, [postRequest]);

  const getOllamaModels = useCallback(async (): Promise<string[]> => {
    return getRequest('/models?provider=ollama');
  }, [postRequest]);

  return {
    sendChatMessage,
    configureModel,
    addToolsToModel,
    getOllamaModels,
  };
}