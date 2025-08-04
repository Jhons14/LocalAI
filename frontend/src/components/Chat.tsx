import { ChatOutput } from '@/components/ChatOutput';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ChatInput } from '@/components/ChatInput';
import { TopNavBar } from '@/components/TopNavBar';
import { ChatErrorBoundary } from '@/components/ChatErrorBoundary';
import { ToastContainer } from '@/components/Toast';
import { useToast } from '@/hooks/useToast';
import { useMobileFirst } from '@/hooks/useResponsive';

export function Chat() {
  const { activeModel } = useChatHistoryContext();
  const { toasts, removeToast } = useToast();
  const { isMobile } = useMobileFirst();

  return (
    <ChatErrorBoundary>
      <div className='flex flex-col h-screen w-full relative'>
        <TopNavBar />
        <div className='flex-1 flex flex-col overflow-hidden'>
          <ChatOutput thread_id={activeModel?.thread_id} />
          {activeModel?.model && (
            <div className={`${isMobile ? 'p-2' : 'p-4'}`}>
              <ChatInput thread_id={activeModel?.thread_id} />
            </div>
          )}
        </div>
        <ToastContainer toasts={toasts} onClose={removeToast} />
      </div>
    </ChatErrorBoundary>
  );
}
