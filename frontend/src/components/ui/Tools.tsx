import { useState, useRef, useEffect } from 'react';
import type { ActiveModel, ToolName } from '@/types/chat';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ToggleSwitch } from '@/components/ui/ToggleSwitch';
import { Hammer, Mail } from 'lucide-react';

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

// Available tools configuration
const AVAILABLE_TOOLS: ToolName[] = ['Gmail', 'Asana'];

// Tools state management hook
function useToolsState(activeModel: ActiveModel | undefined) {
  const [toolsState, setToolsState] = useState<Record<ToolName, boolean>>(() => {
    // Initialize with default false values
    return AVAILABLE_TOOLS.reduce((acc, tool) => {
      acc[tool] = false;
      return acc;
    }, {} as Record<ToolName, boolean>);
  });

  const { setActiveModel } = useChatHistoryContext();

  // Synchronize tools state with activeModel.toolkits
  useEffect(() => {
    if (!activeModel) {
      // Reset all tools when no active model
      setToolsState(prev => {
        const newState = { ...prev };
        AVAILABLE_TOOLS.forEach(tool => {
          newState[tool] = false;
        });
        return newState;
      });
      return;
    }

    // Update tools state based on activeModel.toolkits
    setToolsState(prev => {
      const newState = { ...prev };
      AVAILABLE_TOOLS.forEach(tool => {
        newState[tool] = activeModel.toolkits.includes(tool);
      });
      return newState;
    });
  }, [activeModel?.toolkits, activeModel?.model, activeModel?.provider]);

  const toggleTool = (tool: ToolName, value: boolean) => {
    if (!activeModel) return;

    // Update local state
    setToolsState(prev => ({
      ...prev,
      [tool]: value,
    }));

    // Calculate new toolkits array
    const newToolkits: string[] = [];
    AVAILABLE_TOOLS.forEach(t => {
      const isEnabled = t === tool ? value : toolsState[t];
      if (isEnabled) {
        newToolkits.push(t);
      }
    });

    // Update active model with new toolkits
    setActiveModel({
      ...activeModel,
      toolkits: newToolkits,
    });
  };

  return {
    toolsState,
    toggleTool,
  };
}

// Email button component
function EmailButton() {
  const { userEmail, setUserEmail } = useChatHistoryContext();
  const [isEditingEmail, setIsEditingEmail] = useState(false);
  const [tempEmail, setTempEmail] = useState(userEmail);

  // Update tempEmail when userEmail changes
  useEffect(() => {
    setTempEmail(userEmail);
  }, [userEmail]);

  const handleEmailSubmit = () => {
    if (tempEmail.trim()) {
      setUserEmail(tempEmail.trim());
      setIsEditingEmail(false);
    }
  };

  const handleCancel = () => {
    setTempEmail(userEmail);
    setIsEditingEmail(false);
  };

  if (isEditingEmail) {
    return (
      <div className="flex items-center gap-2 bg-[#333333] border border-[#999999] rounded-lg p-2">
        <Mail size={16} />
        <input
          type="email"
          value={tempEmail}
          onChange={(e) => setTempEmail(e.target.value)}
          placeholder="Enter your email"
          className="bg-transparent text-white text-sm outline-none w-40"
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleEmailSubmit();
            if (e.key === 'Escape') handleCancel();
          }}
          autoFocus
        />
        <button
          onClick={handleEmailSubmit}
          className="text-green-500 hover:text-green-400 text-sm"
        >
          ✓
        </button>
        <button
          onClick={handleCancel}
          className="text-red-500 hover:text-red-400 text-sm"
        >
          ✕
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={() => setIsEditingEmail(true)}
      className="h-full cursor-pointer hover:bg-[#777777] transition-all duration-200 bg-[#555555] rounded-lg p-2 flex items-center gap-2"
      aria-label="Set email"
      title={userEmail || "Set your email"}
    >
      <Mail size={16} />
      {userEmail && (
        <span className="text-sm text-gray-300 max-w-24 truncate">
          {userEmail}
        </span>
      )}
    </button>
  );
}

interface ToolsProps {
  model: ActiveModel | undefined;
}

export function Tools({ model }: ToolsProps) {
  const { isOpen, toggle, ref } = useToggleOutside();
  const { toolsState, toggleTool } = useToolsState(model);

  if (!model) return null;

  const renderTools = () => {
    if (!isOpen) return null;
    
    return (
      <ul className='absolute flex flex-col -left-20 bg-[#333333] text-center w-max border border-[#999999] rounded-xl shadow-lg mt-2 p-1'>
        {AVAILABLE_TOOLS.map((tool) => (
          <li
            key={tool}
            className='flex justify-between items-center gap-2 px-2'
          >
            <label 
              htmlFor={`tool-${tool}`}
              className="cursor-pointer select-none"
            >
              {tool}
            </label>
            <ToggleSwitch
              id={`tool-${tool}`}
              size='x-small'
              value={toolsState[tool]} // Use controlled value instead of initialValue
              onChange={(value) => toggleTool(tool, value)}
              aria-label={`Toggle ${tool} tool`}
            />
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="flex items-center gap-2">
      <EmailButton />
      <div ref={ref} className='relative'>
        <button
          className='h-full cursor-pointer hover:bg-[#777777] transition-all duration-200 bg-[#555555] rounded-lg p-2'
          onClick={toggle}
          aria-label='Tools'
          aria-expanded={isOpen}
          type="button"
        >
          <Hammer />
        </button>
        {renderTools()}
      </div>
    </div>
  );
}