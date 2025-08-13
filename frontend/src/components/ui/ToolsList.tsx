import { useState, useRef, useEffect } from 'react';
import type { ModelName } from '@/types/chat';
import { useChatApi } from '@/hooks/useChatApi';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
function useToggleOutside() {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (ref.current && target && !ref.current.contains(target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  });

  const toggle = () => setIsOpen(!isOpen);

  return { isOpen, toggle, ref };
}

export function ToolsList({ model }: { model: ModelName }) {
  const tools = ['Gmail', 'Asana'];
  const { isOpen, toggle, ref } = useToggleOutside();
  const { addToolsToModel } = useChatApi();
  const { activeModel } = useChatHistoryContext();
  const addTools = async () => {
    if (!activeModel) return;
    const thread_id = activeModel.thread_id;

    try {
      if (!thread_id) return;

      const res = await addToolsToModel({ thread_id });

      console.log(res);
    } catch (err: any) {
      console.error('Error agregando tools al modelo: ' + err);
    }
  };

  console.log(activeModel);

  const renderTools = () => {
    if (!isOpen) return null;
    return (
      <ul className='absolute flex flex-col top-full w-full bg-[#333333] text-center border border-[#999999] rounded shadow-lg mt-1 p-1'>
        {tools.map((tool) => (
          <li key={tool}>
            <button
              onClick={addTools}
              className='cursor-pointer w-full hover:bg-[#555555] transition-all duration-200'
            >
              {tool}
            </button>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div ref={ref} className='relative'>
      <button
        className='w-full cursor-pointer h-10 hover:bg-[#777777] transition-all duration-200 bg-[#555555] rounded-lg'
        onClick={toggle}
        aria-label='Tools'
        aria-expanded={isOpen}
      >
        Tools
      </button>
      {renderTools()}
    </div>
  );
}
