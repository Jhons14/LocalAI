import { ChatOutput } from './ChatOutput';
import { useChatHistoryContext } from '../context/ChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { ChatInput } from './ChatInput';
import { TopNavBar } from './TopNavBar';

export function Chat() {
  const { activeModel } = useChatHistoryContext();
  return (
    <div className='flex flex-col h-screen w-full relative '>
      <TopNavBar />
      <ChatOutput thread_id={activeModel.thread_id} />
      <ChatInput thread_id={activeModel.thread_id} />
    </div>
  );
}
