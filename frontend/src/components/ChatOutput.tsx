import { motion, AnimatePresence } from 'framer-motion';
import { useRef, useState, useEffect, memo, useCallback, useMemo } from 'react';
import { MdEdit, MdSend, MdClose } from 'react-icons/md';
import { marked } from 'marked';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import type { ChatOutputProps, AssistantMessageOutputProps, UserMessageOutputProps } from '@/types/components';

import 'highlight.js/styles/tomorrow-night-blue.min.css';

export const ChatOutput = memo(function ChatOutput({ thread_id }: ChatOutputProps) {
  const { messages } = useChatHistoryContext(); // Obtener la función sendMessage del contexto

  return (
    <div className='flex-1  overflow-y-auto '>
      <div className='flex justify-center'>
        <div className='w-full max-w-[1000px] px-4 py-2 space-y-2'>
          <AnimatePresence>
            {messages.map((msg) => {
              return (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 1 }}
                  transition={{ duration: 1 }}
                >
                  {msg.role === 'assistant' ? (
                    <AssistantMessageOutput
                      key={msg.id}
                      content={msg.content}
                    />
                  ) : (
                    <UserMessageOutput
                      key={msg.id}
                      msg={msg}
                      thread_id={thread_id}
                    />
                  )}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
});

const AssistantMessageOutput = memo(function AssistantMessageOutput({ content }: AssistantMessageOutputProps) {
  const bottomRef = useRef<HTMLDivElement>(null); // 🔽 Este es el marcador de scroll
  const containerRef = useRef<Element>(null);

  useEffect(() => {
    if (content) {
      const dirty = marked(content);
      const clean = DOMPurify.sanitize(dirty);
      if (containerRef.current) {
        containerRef.current.innerHTML = clean;
        // Highlight dinámico de todos los bloques <code>
        containerRef.current.querySelectorAll('pre code').forEach((block) => {
          hljs.highlightElement(block);
          block.parentElement?.classList.add('my-4');
          block.classList.add('rounded-xl', 'border-1', 'border-white/50');
        });
      }
    }

    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [content]);

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
  const [isEditingId, setIsEditingId] = useState<String | null>(null);
  const editMsgTextAreaRef = useRef<HTMLTextAreaElement>(null);

  const handleEditSubmit = useCallback(() => {
    if (!editMsgTextAreaRef.current?.value || !thread_id) return;
    edit(
      msg.id,
      editMsgTextAreaRef.current.value,
      thread_id
    );
    setIsEditingId(null);
  }, [edit, msg.id, thread_id]);

  const handleEditToggle = useCallback(() => {
    setIsEditingId(isEditingId === msg.id ? null : msg.id);
  }, [isEditingId, msg.id]);
  if (msg.id === isEditingId) {
    return (
      <div className='flex-1  flex flex-col items-end'>
        <textarea
          ref={editMsgTextAreaRef}
          className='focus:outline-0 resize-none text-sm leading-relaxed px-4 py-2 rounded-xl text-white w-[200px] bg-gray-500/50'
          defaultValue={msg.content}
        />
        <div className='flex justify-between my-2'>
          <button
            className='py-1 px-2 cursor-pointer hover:bg-gray-500/30 rounded'
            onClick={() => setIsEditingId(null)}
          >
            <MdClose size={20} />
          </button>
          <button
            className='py-1 px-2 cursor-pointer hover:bg-gray-500/30 rounded'
            onClick={handleEditSubmit}
          >
            <MdSend size={20} />
          </button>
        </div>
      </div>
    );
  } else {
    return (
      <div className='flex flex-col items-end'>
        <div className='text-sm leading-relaxed px-4 py-2 rounded-md w-auto bg-gray-600 text-white'>
          <p>{msg.content?.trim()}</p>
          {msg.status === 'streaming' && (
            <span className='animate-blink'>|</span>
          )}
        </div>
        <button
          className='cursor-pointer hover:scale-110 transition-transform duration-200 my-1'
          onClick={handleEditToggle}
          type='button'
        >
          <MdEdit className='hover:fill-amber-50 text-gray-500' size={20} />
        </button>
      </div>
    );
  }
});
