import { Chat } from './chat/Chat';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatHistoryContextProvider } from '@/context/ChatHistoryContext';
import { ToastProvider } from '@/context/ToastContext';
import { AuthProvider } from '@/context/AuthContext';

export function Welcome() {
  return (
    <AuthProvider>
      <ToastProvider>
        <ChatHistoryContextProvider>
          <div className='flex flex-col h-screen'>
            <main className='flex flex-row flex-1'>
              <Sidebar />
              <Chat />
            </main>
          </div>
        </ChatHistoryContextProvider>
      </ToastProvider>
    </AuthProvider>
  );
}
