import { ChatOutput } from '@/components/ChatOutput';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { ChatInput } from '@/components/ChatInput';
import { TopNavBar } from '@/components/TopNavBar';

export function Chat() {
  const { activeModel } = useChatHistoryContext();
  console.log(activeModel);

  return (
    <div className='flex flex-col h-screen w-full relative '>
      <TopNavBar />
      <ChatOutput thread_id={activeModel.thread_id} />
      <ChatInput thread_id={activeModel.thread_id} />
    </div>
  );
}
