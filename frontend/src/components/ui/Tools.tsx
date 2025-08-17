import { useState, useRef, useEffect } from 'react';
import type { ActiveModel, ToolName } from '@/types/chat';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ToggleSwitch } from '@/components/ui/ToggleSwitch';
import { Hammer } from 'lucide-react';

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

export function Tools({ model }: { model: ActiveModel | undefined }) {
  const tools = Object.keys(TOOLS);

  const { isOpen, toggle, ref } = useToggleOutside();
  const { setActiveModel } = useChatHistoryContext();
  if (!model) return null;

  const handleTools = (tool: ToolName, value: boolean) => {
    TOOLS[tool] = value;
    if (!model) return;

    const toolkits: ToolName[] = [];
    for (const [key, value] of Object.entries(TOOLS)) {
      if (value) {
        toolkits.push(key as ToolName);
      }
    }

    setActiveModel({ ...model, toolkits });
  };

  const renderTools = () => {
    if (!isOpen) return null;
    return (
      <ul className='absolute flex flex-col -left-20 bg-[#333333] text-center w-max border border-[#999999] rounded-xl shadow-lg mt-2 p-1'>
        {tools.map((tool) => (
          <li
            key={tool}
            className='flex justify-between items-center gap-2 px-2 '
          >
            <label>{tool}</label>
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
        className='h-full cursor-pointer hover:bg-[#777777] transition-all duration-200 bg-[#555555] rounded-lg p-2'
        onClick={toggle}
        aria-label='Tools'
        aria-expanded={isOpen}
      >
        <Hammer />
      </button>
      {renderTools()}
    </div>
  );
}
