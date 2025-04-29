import type { JSX } from 'react';
import { useChatHistoryContext } from '@/context/ChatHistoryContext';
import { useEffect, useState } from 'react';
import { log } from 'node_modules/astro/dist/core/logger/core';

type subItemType = {
  title: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano';
  provider: 'ollama' | 'openai';
  api_key?: string;
};

type itemType = {
  name: string;
  icon: JSX.Element;
  subItems?: subItemType[];
};

export function SidebarItem({
  item,
  isBarOpen,
  setIsBarOpen,
}: {
  item: itemType;
  isBarOpen: boolean;
  setIsBarOpen: (isBarOpen: boolean) => void;
}) {
  const [isItemOpen, setIsItemOpen] = useState(false);
  const { activeModel, setActiveModel, configureModel } =
    useChatHistoryContext(); // Obtener la función sendMessage del contexto

  useEffect(() => {
    if (!isBarOpen) {
      setIsItemOpen(false);
    }
  }, [isBarOpen]);

  const handleClick = ({
    model,
    provider,
  }: {
    model: 'qwen2.5:3b' | 'gpt-4.1-nano';
    provider: 'ollama' | 'openai';
  }) => {
    const newActiveModel = {
      model: model,
      provider: provider,
    };

    if (newActiveModel.model === activeModel.model) {
      return;
    }

    setActiveModel(newActiveModel);
    configureModel({
      model: newActiveModel.model,
      provider: newActiveModel.provider,
    });
  };

  return (
    <div className='flex flex-col'>
      <button
        className='flex items-center gap-2 p-4 hover:bg-gray-800  w-full cursor-pointer'
        type='button'
        onClick={() => {
          setIsBarOpen(true), setIsItemOpen(!isItemOpen);
        }}
      >
        <div>{item.icon}</div>

        {isBarOpen && <span>{item.name}</span>}
      </button>
      {isItemOpen &&
        isBarOpen &&
        item.subItems?.map((subItem) => (
          <button
            key={subItem.title}
            className={`flex items-center justify-center cursor-pointer py-1 w-full hover:bg-gray-800 transition-all duration-500 ${
              activeModel.model === subItem.model && 'bg-gray-800'
            }`}
            type='button'
            onClick={() =>
              handleClick({ model: subItem.model, provider: subItem.provider })
            }
          >
            <span className='text-gray-400'>{subItem.title}</span>
          </button>
        ))}
    </div>
  );
}
