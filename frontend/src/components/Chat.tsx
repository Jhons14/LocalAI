import { ChatOutput } from '@/components/ChatOutput';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ChatInput } from '@/components/ChatInput';
import { TopNavBar } from '@/components/TopNavBar';
import { ChatErrorBoundary } from '@/components/ChatErrorBoundary';
import { ToastContainer } from '@/components/Toast';
import { useToast } from '@/hooks/useToast';

export function Chat() {
  const { activeModel } = useChatHistoryContext();
  const { toasts, removeToast } = useToast();

  return (
    <ChatErrorBoundary>
      <div className='flex flex-col h-screen w-full relative '>
        <TopNavBar />
        <ChatOutput thread_id={activeModel?.thread_id} />
        {activeModel?.model && <ChatInput thread_id={activeModel?.thread_id} />}
        <ToastContainer toasts={toasts} onClose={removeToast} />
      </div>
    </ChatErrorBoundary>
  );
}
