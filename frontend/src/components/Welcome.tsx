import { Chat } from './chat/Chat';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatHistoryContextProvider } from '@/context/ChatHistoryContext';
import { ToastProvider } from '@/context/ToastContext';

export function Welcome() {
  return (
    <ToastProvider>
      <ChatHistoryContextProvider>
        <main className='flex flex-row h-screen'>
          <Sidebar />
          <Chat />
        </main>
      </ChatHistoryContextProvider>
    </ToastProvider>
  );
}
