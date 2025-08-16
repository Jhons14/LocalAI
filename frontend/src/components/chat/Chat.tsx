import { ChatOutput } from './ChatOutput';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ChatInput } from './ChatInput';
import { TopNavBar } from '@/components/layout/TopNavBar';
import { ChatErrorBoundary } from './ChatErrorBoundary';
import { ToastContainer } from '@/components/ui/Toast';
import { useToast } from '@/hooks/useToast';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useSkipToContent, useAriaLive } from '@/hooks/useAccessibility';

export function Chat() {
  const { activeModel } = useChatHistoryContext();
  const { toasts, removeToast } = useToast();
  const { isMobile } = useMobileFirst();
  const { announceToScreenReader } = useAriaLive();

  // useSkipToContent();

  return (
    <ChatErrorBoundary>
      <div className='flex flex-col h-screen w-full relative'>
        <header role='banner'>
          <TopNavBar />
        </header>
        <main
          id='main-content'
          className='flex-1 flex flex-col overflow-hidden'
          role='main'
          aria-label='Chat conversation'
        >
          <ChatOutput thread_id={activeModel?.thread_id} />
          {activeModel?.model && (
            <div
              className={`${isMobile ? 'p-2' : 'p-4'}`}
              role='region'
              aria-label='Message input'
            >
              <ChatInput thread_id={activeModel?.thread_id} />
            </div>
          )}
        </main>
        <div role='region' aria-label='Notifications' aria-live='polite'>
          <ToastContainer toasts={toasts} onClose={removeToast} />
        </div>
      </div>
    </ChatErrorBoundary>
  );
}
