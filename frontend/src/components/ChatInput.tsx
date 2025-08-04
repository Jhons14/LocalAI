import { useRef, memo, useCallback } from 'react';
import { MdSend } from 'react-icons/md';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import type { ChatInputProps } from '@/types/components';

export const ChatInput = memo(function ChatInput({ thread_id }: ChatInputProps) {
  const { sendMessage } = useChatHistoryContext();
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
    <div className='bottom-0  p-4 border-t border-gray-500'>
      <form
        className='flex items-end border-2 p-2 border-gray-500 rounded-lg'
        onSubmit={handleSubmit}
      >
        <textarea
          className='w-full focus:outline-0 resize-none px-2 overflow-y-auto'
          placeholder='Ask something...'
          ref={chatInputRef}
          onKeyDown={handleKeyDown}
        />
        <button
          className='right-0 border-2 border-gray-500  py-1 px-3 rounded-lg my-auto mx-2  bg-gray-500 hover:bg-gray-700 cursor-pointer '
          type='submit'
        >
          <MdSend size={20} />
        </button>
      </form>
    </div>
  );
});
