import { createContext, useState, useEffect, useRef, useCallback } from 'react';
import { v4 as uuid } from 'uuid';
import { useChatApi } from '@/hooks/useChatApi';
import {
  usePersistentChatHistory,
  usePersistentActiveModel,
  useStorageMaintenance,
} from '@/hooks/usePersistentState';
import type {
  ChatMessage,
  ChatContextValue,
  SendMessageParams,
  ModelName,
  ModelProvider,
} from '@/types/chat';

export const ChatHistoryContext = createContext<ChatContextValue | undefined>(
  undefined
);

export function ChatHistoryContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sendChatMessage } = useChatApi();
  const { saveChatHistory, loadChatHistory } = usePersistentChatHistory();
  const { activeModel, setActiveModel } = usePersistentActiveModel();
  const { checkStorageUsage } = useStorageMaintenance();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isModelConnected, setIsModelConnected] = useState<boolean>(false);
  const [tempApiKey, setTempApiKey] = useState<string>('');

  const chatManager = useRef<
    Record<string, { thread_id?: string; messages: ChatMessage[] }>
  >({}); // Almacena el historial de mensajes

  // Load messages when active model changes
  useEffect(() => {
    if (activeModel?.thread_id) {
      // Load from persistent storage first
      const persistedMessages = loadChatHistory(activeModel.thread_id);

      if (persistedMessages.length > 0) {
        setMessages(persistedMessages);
        // Also update in-memory cache
        chatManager.current[activeModel.model] = {
          thread_id: activeModel.thread_id,
          messages: persistedMessages,
        };
      } else {
        // Check in-memory cache
        const storedMessages = chatManager.current[activeModel.model]?.messages;
        if (storedMessages) {
          setMessages(storedMessages);
        } else {
          setMessages([]);
        }
      }
    } else {
      setMessages([]);
    }
  }, [activeModel, loadChatHistory]);

  // Save messages to persistent storage when they change
  useEffect(() => {
    if (!activeModel || !activeModel.model || !activeModel.thread_id) return;
    if (messages.length === 0) return;

    // Update in-memory cache
    chatManager.current[activeModel.model] = {
      ...chatManager.current[activeModel.model],
      messages: [...messages],
    };

    // Save to persistent storage
    saveChatHistory(
      activeModel.thread_id,
      messages,
      activeModel.model,
      activeModel.provider
    );

    // Check storage usage periodically
    if (messages.length % 10 === 0) {
      // Check every 10 messages
      checkStorageUsage();
    }
  }, [messages, activeModel, saveChatHistory, checkStorageUsage]);

  const rechargeModel = useCallback(
    (model: ModelName, provider: ModelProvider) => {
      if (model in chatManager.current) {
        setActiveModel({
          model: model,
          provider: provider,
          thread_id:
            chatManager?.current[model]?.thread_id ||
            activeModel?.thread_id ||
            '',
          // Preserve existing toolkits if switching to a model that has been used before
          toolkits: activeModel?.toolkits || [],
        }); // Actualizar el modelo activo y el thread_id
        if (chatManager.current[model])
          setMessages(chatManager.current[model].messages); // Cargar el historial de mensajes del modelo activo

        setIsModelConnected(true); // Marcar el modelo como conectado
        return;
      }

      setActiveModel({ 
        model, 
        provider, 
        thread_id: uuid(),
        // Initialize with empty toolkits for new models
        toolkits: [],
      }); // Actualizar el modelo activo y el x

      setIsModelConnected(false);
    },
    [activeModel, setActiveModel]
  );

  // Función para enviar un mensaje al modelo
  const sendMessage = useCallback(
    async ({
      content,
      thread_id,
      model,
      provider,
      api_key,
      toolkits = [],
      enable_memory = true,
    }: SendMessageParams) => {
      if (!thread_id) {
        throw new Error('Please select a model');
      }
      console.log(api_key);

      const id = uuid();
      const userMessage: ChatMessage = {
        id,
        role: 'user',
        content,
        createdAt: Date.now(),
      };

      const assistantMessage: ChatMessage = {
        id: uuid(),
        role: 'assistant',
        content: '',
        relatedTo: id,
        createdAt: Date.now(),
        status: 'streaming',
      };

      setMessages((prev) => [...prev, userMessage, assistantMessage]);

      await sendChatMessage(
        {
          content,
          thread_id,
          model,
          provider,
          toolkits,
          enable_memory,
          api_key,
        },
        // onChunk
        (chunk: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, content: (msg.content || '') + chunk }
                : msg
            )
          );
        },
        // onError
        (error: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, status: 'error' as const, content: error }
                : msg
            )
          );
        },
        // onComplete
        () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessage.id
                ? { ...msg, status: 'complete' as const }
                : msg
            )
          );
        }
      );
    },
    [sendChatMessage, activeModel?.toolkits, tempApiKey]
  );

  const edit = useCallback(
    async (userMessageId: string, newContent: string, thread_id: string) => {
      const userMsg = messages.find((msg) => msg.id === userMessageId);
      const assistantMessage = messages.find(
        (msg) => msg.relatedTo === userMessageId
      );

      if (!userMsg) return;

      const id = uuid();
      const newUserMessage: ChatMessage = {
        id,
        role: 'user',
        content: newContent,
        createdAt: Date.now(),
        edited: true,
      };
      const newAssistantMessage: ChatMessage = {
        id: uuid(),
        role: 'assistant',
        content: '',
        relatedTo: id,
        createdAt: Date.now(),
        status: 'streaming',
      };

      setMessages((prev) =>
        prev.map((msg) => {
          if (msg.id === userMessageId) return newUserMessage;
          if (msg.id === assistantMessage?.id) return newAssistantMessage;
          return msg;
        })
      );

      await sendChatMessage(
        { content: newContent, thread_id },
        // onChunk
        (chunk: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === newAssistantMessage.id
                ? { ...msg, content: (msg.content || '') + chunk }
                : msg
            )
          );
        },
        // onError
        (error: string) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === newAssistantMessage.id
                ? { ...msg, status: 'error' as const, content: error }
                : msg
            )
          );
        },
        // onComplete
        () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === newAssistantMessage.id
                ? { ...msg, status: 'complete' as const }
                : msg
            )
          );
        }
      );
    },
    [messages, sendChatMessage]
  );

  const clear = useCallback(() => {
    setMessages([]);
    // Also clear from persistent storage if we have an active model
    if (activeModel?.thread_id) {
      saveChatHistory(
        activeModel.thread_id,
        [],
        activeModel.model,
        activeModel.provider
      );
    }
  }, [activeModel, saveChatHistory]);

  return (
    <ChatHistoryContext.Provider
      value={{
        messages,
        sendMessage,
        edit,
        clear,
        activeModel,
        setActiveModel,
        tempApiKey,
        setTempApiKey,
        isModelConnected,
        setIsModelConnected,
        rechargeModel,
      }}
    >
      {children}
    </ChatHistoryContext.Provider>
  );
}
