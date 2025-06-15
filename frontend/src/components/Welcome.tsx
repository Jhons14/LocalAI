import { Chat } from './Chat.tsx';
import { Sidebar } from '@/components/Sidebar';
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
