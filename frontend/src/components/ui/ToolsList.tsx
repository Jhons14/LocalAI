import { useState, useRef, useEffect } from 'react';
import type { ModelName, ToolName } from '@/types/chat';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ToggleSwitch } from '@/components/ui/ToggleSwitch';
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

const TOOLS = {
  Gmail: false,
  Asana: false,
};

export function ToolsList({ model }: { model: ModelName }) {
  const tools = Object.keys(TOOLS);

  const { isOpen, toggle, ref } = useToggleOutside();
  const { activeModel, setActiveModel } = useChatHistoryContext();

  const handleTools = (tool: ToolName, value: boolean) => {
    TOOLS[tool] = value;
    if (!activeModel) return;

    const toolkits: ToolName[] = [];
    for (const [key, value] of Object.entries(TOOLS)) {
      if (value) {
        toolkits.push(key as ToolName);
      }
    }

    setActiveModel({ ...activeModel, toolkits });
  };

  const renderTools = () => {
    if (!isOpen) return null;
    return (
      <ul className='absolute flex flex-col top-full w-full bg-[#333333] text-center border border-[#999999] rounded-xl shadow-lg mt-1 p-1'>
        {tools.map((tool) => (
          <li key={tool} className='flex justify-between items-center w-full'>
            <label className='cursor-pointer w-full hover:bg-[#555555] transition-all duration-200'>
              {tool}
            </label>
            <ToggleSwitch
              size='x-small'
              initialValue={TOOLS[tool as ToolName]}
              onChange={(value) => {
                handleTools(tool as ToolName, value);
              }}
            />
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
