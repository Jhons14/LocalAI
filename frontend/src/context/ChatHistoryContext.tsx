import { createContext, useState, useEffect, useRef } from 'react';
import { v4 as uuid } from 'uuid';
import { useChatApi } from '@/hooks/useChatApi';
import type { 
  ChatMessage, 
  ActiveModel, 
  ChatContextValue, 
  SendMessageParams, 
  ConfigureModelParams,
  ModelName,
  ModelProvider
} from '@/types/chat';

export const ChatHistoryContext = createContext<
  ChatContextValue | undefined
>(undefined);

export function ChatHistoryContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { sendChatMessage, configureModel: apiConfigureModel } = useChatApi();
  
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isModelConnected, setIsModelConnected] = useState<boolean>(false);
  const [tempApiKey, setTempApiKey] = useState<string>('');

  const [activeModel, setActiveModel] = useState<ActiveModel | undefined>(
    undefined
  );

  useEffect(() => {
    // configureModel({
    //   model: activeModel.model,
    //   provider: activeModel.provider,
    // });
  }, []);

  const chatManager = useRef<
    Record<string, { thread_id: string; messages: ChatMessage[] }>
  >({}); // Almacena el historial de mensajes

  useEffect(() => {
    if (activeModel) {
      const storedMessages = chatManager.current[activeModel.model]?.messages;
      if (storedMessages) {
        setMessages(storedMessages); // Cargar el historial de mensajes del modelo activo
      } else {
        setMessages([]); // Limpiar los mensajes si no hay historial
      }
    }
  }, [activeModel]);

  useEffect(() => {
    if (!activeModel || !activeModel.model) return;
    if (!chatManager.current[activeModel.model]) return;

    chatManager.current[activeModel.model] = {
      ...chatManager.current[activeModel.model],
      messages: [...messages],
    }; // Actualizar el historial de mensajes en el chatManager
  }, [messages]); // Dependencia añadida para cargar mensajes al cambiar de modelo

  const rechargeModel = (
    model: ModelName,
    provider: ModelProvider
  ) => {
    if (model in chatManager.current) {
      setActiveModel({
        model: model,
        provider: provider,
        thread_id:
          chatManager?.current[model]?.thread_id ||
          activeModel?.thread_id ||
          '',
      }); // Actualizar el modelo activo y el thread_id
      setMessages(chatManager.current[model].messages); // Cargar el historial de mensajes del modelo activo

      setIsModelConnected(true); // Marcar el modelo como conectado
      return;
    }

    setActiveModel({ model, provider, thread_id: uuid() }); // Actualizar el modelo activo y el x
    setIsModelConnected(false); // Marcar el modelo como conectado
  };

  const configureModel = async ({
    model,
    provider,
    connectModel,
  }: ConfigureModelParams) => {
    if (!model || !provider) {
      throw new Error('Please select a model and provider');
    }

    if (connectModel === false) return;

    const thread_id = activeModel?.thread_id || uuid();
    setIsModelConnected(false);

    if (provider === 'openai' && tempApiKey === '') {
      alert('Please save your API key first');
      return;
    }

    try {
      await apiConfigureModel({
        model,
        provider,
        thread_id,
        apiKey: tempApiKey,
      });

      chatManager.current[model] = {
        thread_id,
        messages: [],
      };

      setIsModelConnected(true);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Configuration failed';
      alert(errorMessage);
      throw error;
    }
  };

  // Función para enviar un mensaje al modelo
  const sendMessage = async ({
    content,
    thread_id,
  }: SendMessageParams) => {
    if (!thread_id) {
      throw new Error('Please select a model');
    }

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
      { content, thread_id },
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
  };

  const edit = async (
    userMessageId: string,
    newContent: string,
    thread_id: string
  ) => {
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
  };
  const clear = () => setMessages([]);

  return (
    <ChatHistoryContext.Provider
      value={{
        messages,
        sendMessage,
        edit,
        clear,
        activeModel,
        setActiveModel,
        configureModel,
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
