import { createContext, useState, useEffect, useRef } from 'react';
import { v4 as uuid } from 'uuid';

type ChatMessageType = {
  id: string;
  role: 'user' | 'assistant';
  content?: string; // Cambiado a string[] para almacenar los chunks
  status?: 'complete' | 'streaming' | 'error';
  relatedTo?: string; // Para enlazar respuestas con preguntas
  edited?: boolean;
  createdAt: number;
};

type ActiveModelType = {
  thread_id: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano' | '';
  provider: 'ollama' | 'openai' | '';
  api_key?: string;
};

export type ChatHistoryContextType = {
  messages: ChatMessageType[];
  sendMessage: ({ content }: { content: string; thread_id: string }) => void;
  edit: (userMessageId: string, newContent: string, thread_id: string) => void;
  clear: () => void;
  activeModel: ActiveModelType;
  setActiveModel: React.Dispatch<React.SetStateAction<ActiveModelType>>;
  configureModel: ({
    model,
    provider,
    api_key,
  }: {
    model: ActiveModelType['model'];
    provider: ActiveModelType['provider'];
    api_key?: ActiveModelType['api_key'];
  }) => Promise<void>;
  isModelConnected: boolean;
  isApiKeySaved: boolean;
  setIsApiKeySaved: (isApiKeySaved: boolean) => void;
};

export const ChatHistoryContext = createContext<
  ChatHistoryContextType | undefined
>(undefined);

export function ChatHistoryContextProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const BACKEND_URL = 'http://127.0.0.1:8000';
  const [isApiKeySaved, setIsApiKeySaved] = useState<boolean>(false);
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [activeModel, setActiveModel] = useState<ActiveModelType>({
    thread_id: uuid(),
    model: '',
    provider: '',
  });

  useEffect(() => {
    configureModel({
      model: activeModel.model,
      provider: activeModel.provider,
    });
  }, []);

  const [isModelConnected, setIsModelConnected] = useState<boolean>(false);

  const controllerRef = useRef<AbortController | null>(null);

  const chatManager = useRef<
    Record<string, { thread_id: string; messages: ChatMessageType[] }>
  >({}); // Almacena el historial de mensajes

  useEffect(() => {
    if (activeModel.model) {
      const storedMessages = chatManager.current[activeModel.model]?.messages;
      if (storedMessages) {
        setMessages(storedMessages); // Cargar el historial de mensajes del modelo activo
      } else {
        setMessages([]); // Limpiar los mensajes si no hay historial
      }
    }
  }, [activeModel.model]);

  useEffect(() => {
    chatManager.current[activeModel.model] = {
      ...chatManager.current[activeModel.model],
      messages: [...messages],
    }; // Actualizar el historial de mensajes en el chatManager
  }, [messages]); // Dependencia añadida para cargar mensajes al cambiar de modelo

  const configureModel = async ({
    model,
    provider,
    api_key,
  }: {
    model: ActiveModelType['model'];
    provider: ActiveModelType['provider'];
    api_key?: ActiveModelType['api_key'];
  }) => {
    await fetch(BACKEND_URL + '/keys', {
      method: 'get',
      headers: {
        'Content-Type': 'application/json',
      },
    }).then(async (res) => {
      if (!res.ok) {
        throw new Error('Network response was not ok');
      }
      const keys = await res.json();

      setIsApiKeySaved(provider in keys ? true : false);
      if (model === 'gpt-4.1-nano' && provider in keys === false) {
        throw new Error('There is not key saved for the model ' + model);
      }
    });

    if (model in chatManager.current) {
      setMessages(chatManager.current[model].messages); // Cargar el historial de mensajes del modelo activo

      setActiveModel({
        model: model,
        provider: provider,
        thread_id:
          chatManager.current[model].thread_id || activeModel.thread_id,
      }); // Actualizar el modelo activo y el thread_id
      return;
    }

    controllerRef.current?.abort(); // Cancelar cualquier stream anterior
    const controller = new AbortController();
    controllerRef.current = controller;

    const thread_id = uuid(); // Generar un nuevo thread_id

    setIsModelConnected(false); // Resetear el estado de conexión
    setActiveModel({ model, provider, thread_id }); // Actualizar el modelo activo y el thread_id

    const res = await fetch(`${BACKEND_URL}/configure`, {
      method: 'POST',
      body: JSON.stringify({ thread_id, model, provider, api_key }),
      headers: { 'Content-Type': 'application/json' },
      // signal: controller.signal,
    });

    if (!res.ok) {
      switch (res.status) {
        case 503:
          alert('Service is not available, please try again later');
        case 400:
          const responseText = await res.json().then((data) => data.detail);
          setIsModelConnected(false); // Resetear el estado de conexión
          throw new Error(responseText);
      }
      return;
    }
    chatManager.current[model] = {
      thread_id,
      messages: [], // Reiniciar el historial de mensajes al cambiar de modelo
    }; // Actualizar el historial de mensajes en el chatManager

    setIsModelConnected(true);
  };

  // Función para enviar un mensaje al modelo
  const sendMessage = async ({
    content,
    thread_id,
  }: {
    thread_id: string;
    content: string;
  }) => {
    if (!thread_id) {
      throw new Error('Please select a model');
    }

    const id = uuid();
    const userMessage: ChatMessageType = {
      id,
      role: 'user',
      content,
      createdAt: Date.now(),
    };

    const assistantMessage: ChatMessageType = {
      id: uuid(),
      role: 'assistant',
      content: '',
      relatedTo: id,
      createdAt: Date.now(),
      status: 'streaming',
    };

    setMessages((prev) => [...prev, userMessage, assistantMessage]);

    controllerRef.current?.abort(); // Cancelar cualquier stream anterior
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const res = await fetch(BACKEND_URL + '/chat', {
        method: 'POST',
        body: JSON.stringify({ prompt: content, thread_id: thread_id }),
        headers: {
          'Content-Type': 'application/json',
        },
        // signal: controller.signal,
      });

      if (!res.ok) {
        switch (res.status) {
          case 503:
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessage.id
                  ? {
                      ...msg,
                      status: 'error',
                      content:
                        'Service is not avalaible, please try again later',
                    }
                  : msg
              )
            );
          case 400:
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessage.id
                  ? {
                      ...msg,
                      status: 'error',
                      content:
                        'Invalid request, please connect to the model first',
                    }
                  : msg
              )
            );
        }

        return;
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader available');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessage.id
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id ? { ...msg, status: 'complete' } : msg
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessage.id
            ? { ...msg, status: 'error', content: '[error]' }
            : msg
        )
      );
    }
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
    const newUserMessage: ChatMessageType = {
      id,
      role: 'user',
      content: newContent,
      createdAt: Date.now(),
      edited: true,
    };
    const newAssistantMessage: ChatMessageType = {
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

    controllerRef.current?.abort(); // Cancelar cualquier stream anterior
    const controller = new AbortController();
    controllerRef.current = controller;
    try {
      const res = await fetch(BACKEND_URL + '/chat', {
        method: 'POST',
        body: JSON.stringify({ prompt: newContent, thread_id: thread_id }),
        headers: { 'Content-Type': 'application/json' },
        // signal: controller.signal,
      });
      if (!res.ok) {
        if (res.status === 503) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === newAssistantMessage.id
                ? {
                    ...msg,
                    status: 'error',
                    content: 'Service is not avalaible, please try again later',
                  }
                : msg
            )
          );
        }
        return;
      }
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No reader available');
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });

        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === newAssistantMessage.id
              ? { ...msg, content: msg.content + chunk }
              : msg
          )
        );
      }

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === newAssistantMessage.id
            ? { ...msg, status: 'complete' }
            : msg
        )
      );
    } catch (err) {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === newAssistantMessage.id
            ? { ...msg, status: 'error', content: '[error]' }
            : msg
        )
      );
    }
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
        isModelConnected,
        isApiKeySaved,
        setIsApiKeySaved,
      }}
    >
      {children}
    </ChatHistoryContext.Provider>
  );
}
