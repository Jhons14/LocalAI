import { type JSX, useState } from 'react';
import { Menu } from 'lucide-react';
import { useChatHistoryContext } from '../context/ChatHistoryContext';
import { SidebarItem } from './SidebarItem';
import OpenAILogo from '../assets/OpenAILogo.svg?react';
import OllamaLogo from '../assets/OllamaLogo.svg?react';

type NavType = {
  name: string;
  icon: JSX.Element;
  subItems?: {
    title: string;
    model: 'qwen2.5:3b' | 'gpt-4.1-nano';
    provider: 'ollama' | 'openai';
    api_key?: string;
  }[];
}[];

const navItems: NavType = [
  {
    name: 'Ollama',
    icon: <OllamaLogo className='w-6 h-6  fill-white' />,
    subItems: [
      { title: 'qwen2.5:3b', model: 'qwen2.5:3b', provider: 'ollama' },
    ],
  },
  {
    name: 'OpenAI',
    icon: <OpenAILogo className='w-6 h-6 fill-white' />,
    subItems: [
      { title: 'gpt-4.1-nano', model: 'gpt-4.1-nano', provider: 'openai' },
    ],
  },
];

export function Sidebar() {
  const [isBarOpen, setIsBarOpen] = useState(true);
  return (
    <div
      className={`${
        isBarOpen ? 'w-50' : 'w-14'
      } h-screen bg-gray-900 text-white transition-all duration-400 flex flex-col`}
    >
      <button
        onClick={() => setIsBarOpen(!isBarOpen)}
        className='cursor-pointer p-4 focus:outline-none hover:bg-gray-800'
      >
        <Menu />
      </button>
      <nav className='flex-1'>
        {navItems.map((item) => (
          <SidebarItem
            key={item.name}
            item={item}
            isBarOpen={isBarOpen}
            setIsBarOpen={setIsBarOpen}
          />
        ))}
      </nav>
    </div>
  );
}
