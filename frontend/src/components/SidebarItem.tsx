import type { JSX } from 'react';
import { useEffect } from 'react';

type SubItemType = {
  title: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano';
  provider: 'ollama' | 'openai';
  api_key?: string;
};

type ItemType = {
  name: string;
  icon: JSX.Element;
  subItems?: SubItemType[];
};

export function SidebarItem({
  item,
  isBarOpen,
  setIsBarOpen,
  isItemOpen,
  setIsItemOpen,
  choosedNavItem,
  setChoosedNavItem,
}: {
  item: ItemType;
  isBarOpen: boolean;
  setIsBarOpen: (isBarOpen: boolean) => void;
  isItemOpen: boolean;
  setIsItemOpen: (isBarOpen: boolean) => void;
  choosedNavItem?: ItemType;
  setChoosedNavItem: (choosedNavItem?: ItemType) => void;
}) {
  useEffect(() => {
    if (!isBarOpen) {
      setIsItemOpen(false);
    }
  }, [isBarOpen]);

  return (
    <button
      className={`${
        choosedNavItem === item && 'bg-gray-800'
      } flex items-center gap-2 p-4 hover:bg-gray-800 w-full cursor-pointer`}
      type='button'
      onClick={() => {
        setIsBarOpen(true);
        if (choosedNavItem === item) {
          setIsItemOpen(!isItemOpen);
          return;
        }
        setIsItemOpen(true), setChoosedNavItem(item);
      }}
    >
      <div>{item.icon}</div>

      {isBarOpen && <span className='animate-fade-in'>{item.name}</span>}
    </button>
  );
}
