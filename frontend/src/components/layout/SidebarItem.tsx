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
  isBarOpen,
  setIsBarOpen,
  setIsItemOpen,
  selectedIndex,
  setSelectedIndex,
}: {
  item: NavItemType;
  index: number;
  isBarOpen: boolean;
  setIsBarOpen: (isBarOpen: boolean) => void;
  isItemOpen: boolean;
  setIsItemOpen: (isBarOpen: boolean) => void;
  selectedIndex?: number;
  setSelectedIndex: (index: number) => void;
}) {
  useEffect(() => {
    if (!isBarOpen) {
      setIsItemOpen(false);
    }
  }, [isBarOpen]);

  console.log('Index' + index);
  console.log('selectedIndex' + selectedIndex);

  return (
    <button
      className={`${
        index === selectedIndex && 'bg-[#555555]'
      } flex justify-center items-center gap-2 py-4 px-2 hover:bg-[#555555] w-full cursor-pointer transition-all duration-500`}
      type='button'
      onClick={() => {
        setIsBarOpen(true);
        setIsItemOpen(true);
        setSelectedIndex(index);
      }}
    >
      <div>{item.icon}</div>

      {isBarOpen && <span className='animate-fade-in'>{item.name}</span>}
    </button>
  );
}
