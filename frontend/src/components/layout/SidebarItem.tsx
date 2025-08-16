import type { JSX } from 'react';
import { useEffect } from 'react';

type SubItemType = {
  title: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano';
  provider: 'ollama' | 'openai';
  api_key?: string;
};

type NavItemType = {
  name: string;
  icon: JSX.Element;
  subItems?: SubItemType[];
};

export function SidebarItem({
  item,
  index,
  isItemOpen,
  setIsItemOpen,
  selectedIndex,
  setSelectedIndex,
}: {
  item: NavItemType;
  index: number;
  isItemOpen: boolean;
  setIsItemOpen: (isItemOpen: boolean) => void;
  selectedIndex?: number;
  setSelectedIndex: (index: number) => void;
}) {
  return (
    <button
      className={`${
        index === selectedIndex && 'bg-[#555555]'
      } flex justify-center items-center gap-2 py-4 px-1 hover:bg-[#555555] w-full cursor-pointer transition-all duration-500`}
      type='button'
      onClick={() => {
        if (index === selectedIndex) {
          setIsItemOpen(!isItemOpen);

          return;
        }
        setSelectedIndex(index);
        setIsItemOpen(true);
      }}
    >
      <div>{item.icon}</div>
    </button>
  );
}
