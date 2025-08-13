import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useState, useEffect, memo, useCallback, useMemo } from 'react';
import { MdEdit, MdSend, MdClose } from 'react-icons/md';
import { marked } from 'marked';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import type {
  ChatOutputProps,
  AssistantMessageOutputProps,
  UserMessageOutputProps,
} from '@/types/components';
import type { ChatMessage } from '@/types/chat';
import { TypingIndicator } from '@/components/ui/LoadingStates';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useAriaLive } from '@/hooks/useAccessibility';

import 'highlight.js/styles/tomorrow-night-blue.min.css';

export const ChatOutput = memo(function ChatOutput({
  thread_id,
}: ChatOutputProps) {
  const { messages } = useChatHistoryContext();
  const { isMobile } = useMobileFirst();
  const containerRef = useRef<HTMLDivElement>(null);

  // Virtual scrolling for large message lists
  const ITEMS_TO_RENDER = 50; // Only render last 50 messages for performance
  const visibleMessages = useMemo(() => {
    if (messages.length <= ITEMS_TO_RENDER) {
      return messages;
    }
    return messages.slice(-ITEMS_TO_RENDER);
  }, [messages]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      const container = containerRef.current;
      const isNearBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight <
        100;

      if (isNearBottom) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [messages.length]);

  const renderMessage = useCallback(
    (msg: ChatMessage, index: number) => {
      return (
        <motion.div
          key={msg.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.3 }}
          className='mb-4'
        >
          {msg.role === 'assistant' ? (
            <AssistantMessageOutput content={msg.content} />
          ) : (
            <UserMessageOutput msg={msg} thread_id={thread_id} />
          )}
        </motion.div>
      );
    },
    [thread_id]
  );

  return (
    <div
      className='flex-1 overflow-y-auto'
      ref={containerRef}
      role='log'
      aria-label='Chat conversation history'
      aria-live='polite'
      aria-atomic='false'
    >
      <div className='flex justify-center'>
        <div
          className={`w-full ${isMobile ? 'px-2 py-1' : 'px-4 py-2'} ${
            isMobile ? 'max-w-full' : 'max-w-[1000px]'
          }`}
        >
          {messages.length > ITEMS_TO_RENDER && (
            <div
              className={`text-center text-[#555555] mb-4 p-2 bg-gray-100 rounded ${
                isMobile ? 'text-xs' : 'text-sm'
              }`}
              role='status'
              aria-label={`Showing ${ITEMS_TO_RENDER} of ${messages.length} messages`}
            >
              <div className='mb-1'>
                Showing last {ITEMS_TO_RENDER} of {messages.length} messages
              </div>
              <button
                className={`text-blue-500 hover:text-blue-700 focus:text-blue-700 underline keyboard-navigation touch-friendly ${
                  isMobile ? 'text-xs' : 'text-sm'
                }`}
                onClick={() => {
                  // Could implement "load more" functionality here
                  console.log('Load more messages');
                }}
                aria-label='Load earlier messages from conversation history'
              >
                Load earlier messages
              </button>
            </div>
          )}
          <div role='group' aria-label='Chat messages'>
            <AnimatePresence mode='popLayout'>
              {visibleMessages.map((msg, index) => renderMessage(msg, index))}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
});

const AssistantMessageOutput = memo(function AssistantMessageOutput({
  content,
}: AssistantMessageOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    async function renderContent() {
      if (content) {
        const dirty = await marked.parse(content, {
          breaks: true,
          gfm: true,
        });

        const clean = DOMPurify.sanitize(dirty);

        if (containerRef.current) {
          containerRef.current.innerHTML = clean;

          // Style lists
          containerRef.current.querySelectorAll('ol').forEach((ol) => {
            ol.classList.add(
              'list-decimal',
              'list-inside',
              // 'pl-5',
              'space-y-1',
              'font-bold'
            );
          });

          containerRef.current.querySelectorAll('ol li').forEach((li) => {
            li.classList.add('mb-1');
            // Make content normal weight, keep numbers bold
            li.innerHTML = `<span class="font-normal">${li.innerHTML}</span>`;
          });

          containerRef.current.querySelectorAll('ul').forEach((ul) => {
            ul.classList.add('list-disc', 'list-inside', 'pl-5', 'space-y-1');
          });

          // Highlight code blocks
          containerRef.current.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block as HTMLElement);
            block.parentElement?.classList.add('my-4');
            block.classList.add('rounded-xl', 'border-1', 'border-white/50');
          });
        }
      }

      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    renderContent();
  }, [content]);

  // Show typing indicator if no content yet
  if (!content || content.trim() === '') {
    return (
      <div className='flex-1 overflow-y-auto p-4'>
        <TypingIndicator />
        <div ref={bottomRef} />
      </div>
    );
  }

  return (
    <div className='flex-1 overflow-y-auto'>
      <div
        ref={containerRef}
        className={`flex-1 flex-col text-sm leading-relaxed px-4 py-2 rounded-2xl overflow-y-auto`}
      />
      <div ref={bottomRef} />
    </div>
  );
});

const UserMessageOutput = memo(function UserMessageOutput({
  msg,
  thread_id,
}: UserMessageOutputProps) {
  const { edit } = useChatHistoryContext();
  const { isMobile } = useMobileFirst();
  const [isEditingId, setIsEditingId] = useState<String | null>(null);
  const editMsgTextAreaRef = useRef<HTMLTextAreaElement>(null);

  const handleEditSubmit = useCallback(() => {
    if (!editMsgTextAreaRef.current?.value || !thread_id) return;
    edit(msg.id, editMsgTextAreaRef.current.value, thread_id);
    setIsEditingId(null);
  }, [edit, msg.id, thread_id]);

  const handleEditToggle = useCallback(() => {
    setIsEditingId(isEditingId === msg.id ? null : msg.id);
  }, [isEditingId, msg.id]);
  if (msg.id === isEditingId) {
    return (
      <div className='flex-1 flex flex-col items-end'>
        <textarea
          ref={editMsgTextAreaRef}
          className={`focus:outline-0 resize-none leading-relaxed rounded-xl text-white bg-[#555555]/50 ${
            isMobile
              ? 'text-sm px-3 py-2 w-full max-w-[280px]'
              : 'text-sm px-4 py-2 w-[200px]'
          }`}
          defaultValue={msg.content}
          rows={isMobile ? 3 : 2}
        />
        <div
          className={`flex justify-between my-2 ${
            isMobile ? 'w-full max-w-[280px]' : ''
          }`}
        >
          <button
            className={`cursor-pointer hover:bg-[#555555]/30 rounded touch-friendly ${
              isMobile ? 'py-2 px-3' : 'py-1 px-2'
            }`}
            onClick={() => setIsEditingId(null)}
            aria-label='Cancel edit'
          >
            <MdClose size={isMobile ? 18 : 20} />
          </button>
          <button
            className={`cursor-pointer hover:bg-[#555555]/30 rounded touch-friendly ${
              isMobile ? 'py-2 px-3' : 'py-1 px-2'
            }`}
            onClick={handleEditSubmit}
            aria-label='Save edit'
          >
            <MdSend size={isMobile ? 18 : 20} />
          </button>
        </div>
      </div>
    );
  } else {
    return (
      <div className='flex flex-col items-end'>
        <div
          className={`leading-relaxed rounded-md w-auto bg-gray-600 text-white max-w-[85%] ${
            isMobile ? 'text-sm px-3 py-2 break-words' : 'text-sm px-4 py-2'
          }`}
        >
          <p className='whitespace-pre-wrap'>{msg.content?.trim()}</p>
          {msg.status === 'streaming' && (
            <span className='animate-blink'>|</span>
          )}
        </div>
        <button
          className={`cursor-pointer hover:scale-110 transition-transform duration-200 my-1 touch-friendly ${
            isMobile ? 'p-2' : 'p-1'
          }`}
          onClick={handleEditToggle}
          type='button'
          aria-label='Edit message'
        >
          <MdEdit
            className='hover:fill-amber-50 text-[#555555]'
            size={isMobile ? 18 : 20}
          />
        </button>
      </div>
    );
  }
});
