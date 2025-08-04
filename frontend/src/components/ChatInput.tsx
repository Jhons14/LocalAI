import { useRef, memo, useCallback } from 'react';
import { MdSend } from 'react-icons/md';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useAriaDescribedBy } from '@/hooks/useAccessibility';
import type { ChatInputProps } from '@/types/components';

export const ChatInput = memo(function ChatInput({ thread_id }: ChatInputProps) {
  const { sendMessage } = useChatHistoryContext();
  const { isMobile } = useMobileFirst();
  const { getDescribedBy } = useAriaDescribedBy('chat-input');
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback((event: React.FormEvent) => {
    event.preventDefault();
    if (!chatInputRef.current?.value.trim()) {
      return;
    }
    sendMessage({
      content: chatInputRef.current.value,
      thread_id: thread_id,
    });
    chatInputRef.current.value = '';
  }, [sendMessage, thread_id]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      if (event.currentTarget.value.trim() === '') {
        event.preventDefault();
        return;
      }
      event.preventDefault();
      sendMessage({
        content: event.currentTarget.value,
        thread_id: thread_id,
      });
      event.currentTarget.value = '';
      event.currentTarget.blur();
    }
  }, [sendMessage, thread_id]);

  return (
    <div className={`border-t border-gray-500 ${isMobile ? 'p-2' : 'p-4'}`}>
      <form
        className={`flex items-end border-2 border-gray-500 rounded-lg ${isMobile ? 'p-2' : 'p-3'} bg-white`}
        onSubmit={handleSubmit}
        role="search"
        aria-label="Send message to AI"
      >
        <label htmlFor="message-input" className="sr-only">
          Type your message to the AI assistant
        </label>
        <textarea
          id="message-input"
          className={`w-full focus:outline-0 resize-none keyboard-navigation ${isMobile ? 'px-2 py-1 text-base' : 'px-3 py-2'} overflow-y-auto min-h-[44px] max-h-32`}
          placeholder={isMobile ? 'Ask...' : 'Ask something...'}
          ref={chatInputRef}
          onKeyDown={handleKeyDown}
          rows={isMobile ? 1 : 2}
          aria-describedby={getDescribedBy(['help'])}
          aria-required="true"
        />
        <div id="chat-input-help" className="sr-only">
          Press Enter to send your message, or Shift+Enter for a new line
        </div>
        <button
          className={`border-2 border-gray-500 rounded-lg bg-gray-500 hover:bg-gray-700 focus:bg-gray-700 cursor-pointer transition-colors keyboard-navigation touch-friendly ${isMobile ? 'p-2 ml-2' : 'py-2 px-3 ml-3'}`}
          type='submit'
          aria-label='Send message to AI assistant'
        >
          <MdSend size={isMobile ? 18 : 20} aria-hidden="true" />
        </button>
      </form>
    </div>
  );
});
