import { useRef, memo, useCallback, useState } from 'react';
import { MdSend, MdWarning } from 'react-icons/md';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useAriaDescribedBy } from '@/hooks/useAccessibility';
import { useValidation } from '@/hooks/useValidation';
import { useToast } from '@/hooks/useToast';
import type { ChatInputProps } from '@/types/components';

export const ChatInput = memo(function ChatInput({ thread_id }: ChatInputProps) {
  const { sendMessage } = useChatHistoryContext();
  const { isMobile } = useMobileFirst();
  const { getDescribedBy } = useAriaDescribedBy('chat-input');
  const { validateField, getFieldError, hasFieldError, clearValidation } = useValidation();
  const { error: showError } = useToast();
  const chatInputRef = useRef<HTMLTextAreaElement>(null);
  const [isValidating, setIsValidating] = useState(false);

  const handleSubmit = useCallback(async (event: React.FormEvent) => {
    event.preventDefault();
    if (!chatInputRef.current?.value.trim()) {
      return;
    }

    setIsValidating(true);
    const message = chatInputRef.current.value;
    
    // Validate the message
    const validation = validateField('message', message);
    
    if (!validation.isValid) {
      showError('Invalid Message', validation.errors[0]);
      setIsValidating(false);
      return;
    }

    try {
      // Use sanitized value if available
      const sanitizedMessage = validation.sanitizedValue || message;
      
      await sendMessage({
        content: sanitizedMessage,
        thread_id: thread_id,
      });
      
      chatInputRef.current.value = '';
      clearValidation('message');
    } catch (error) {
      showError('Send Failed', 'Failed to send message. Please try again.');
    } finally {
      setIsValidating(false);
    }
  }, [sendMessage, thread_id, validateField, showError, clearValidation]);

  const handleKeyDown = useCallback((event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event as any);
    }
  }, [handleSubmit]);

  const handleInputChange = useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    const value = event.target.value;
    // Clear validation errors when user starts typing
    if (hasFieldError('message')) {
      clearValidation('message');
    }
  }, [hasFieldError, clearValidation]);

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
          className={`w-full focus:outline-0 resize-none keyboard-navigation ${isMobile ? 'px-2 py-1 text-base' : 'px-3 py-2'} overflow-y-auto min-h-[44px] max-h-32 ${
            hasFieldError('message') ? 'border-red-500 border' : ''
          }`}
          placeholder={isMobile ? 'Ask...' : 'Ask something...'}
          ref={chatInputRef}
          onKeyDown={handleKeyDown}
          onChange={handleInputChange}
          rows={isMobile ? 1 : 2}
          aria-describedby={getDescribedBy(['help', 'error'])}
          aria-required="true"
          aria-invalid={hasFieldError('message')}
        />
        <div id="chat-input-help" className="sr-only">
          Press Enter to send your message, or Shift+Enter for a new line
        </div>
        {hasFieldError('message') && (
          <div id="chat-input-error" className="sr-only" role="alert">
            {getFieldError('message')}
          </div>
        )}
        <button
          className={`border-2 border-gray-500 rounded-lg bg-gray-500 hover:bg-gray-700 focus:bg-gray-700 cursor-pointer transition-colors keyboard-navigation touch-friendly ${isMobile ? 'p-2 ml-2' : 'py-2 px-3 ml-3'} ${
            isValidating ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          type='submit'
          aria-label='Send message to AI assistant'
          disabled={isValidating}
        >
          {isValidating ? (
            <div className="animate-spin rounded-full border-2 border-white border-t-transparent" 
                 style={{ width: isMobile ? 18 : 20, height: isMobile ? 18 : 20 }} />
          ) : (
            <MdSend size={isMobile ? 18 : 20} aria-hidden="true" />
          )}
        </button>
      </form>
      {hasFieldError('message') && (
        <div className="mt-1 flex items-center text-red-600 text-sm">
          <MdWarning size={16} className="mr-1" />
          {getFieldError('message')}
        </div>
      )}
    </div>
  );
});
