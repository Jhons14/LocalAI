import { Chat } from './chat/Chat';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatHistoryContextProvider } from '@/context/ChatHistoryContext';

export function Welcome() {
  return (
    <ChatHistoryContextProvider>
      <main className='flex flex-row h-screen'>
        <Sidebar />
        <Chat />
      </main>
    </ChatHistoryContextProvider>
  );
}
