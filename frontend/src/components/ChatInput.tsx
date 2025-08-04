import { useRef } from 'react';
import { MdSend } from 'react-icons/md';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import type { ChatInputProps } from '@/types/components';

export function ChatInput({ thread_id }: ChatInputProps) {
  const { sendMessage } = useChatHistoryContext(); // Obtener la función sendMessage del contexto
  const chatInputRef = useRef<HTMLTextAreaElement>(null); // Crear una referencia al input

  return (
    <div className='bottom-0  p-4 border-t border-gray-500'>
      <form
        className='flex items-end border-2 p-2 border-gray-500 rounded-lg'
        onSubmit={(event) => {
          event.preventDefault();
          if (!chatInputRef.current?.value) {
            return;
          }
          sendMessage({
            content: chatInputRef.current.value,
            thread_id: thread_id,
          }); // Enviar el mensaje al presionar Enter
          chatInputRef.current.value = ''; // Limpiar el input después de enviar el mensaje
        }}
      >
        <textarea
          className='w-full focus:outline-0 resize-none px-2 overflow-y-auto'
          placeholder='Ask something...'
          ref={chatInputRef} // Asignar la referencia al input
          onKeyDown={(event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
              if (event.currentTarget.value.trim() === '') {
                event.preventDefault();
                return;
              }
              sendMessage({
                content: event.currentTarget.value,
                thread_id: thread_id,
              }); // Enviar el mensaje al presionar Enter
              event.currentTarget.value = ''; // Limpiar el input después de enviar el mensaje
              event.currentTarget.blur(); // Volver a enfocar el input
            }
          }}
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
}
