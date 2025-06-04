import { type JSX, useState } from 'react';
import { Menu } from 'lucide-react';
import { SidebarItem } from './SidebarItem';
import OpenAILogo from '../assets/OpenAILogo.svg?react';
import OllamaLogo from '../assets/OllamaLogo.svg?react';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext'; // Asegúrate de que la ruta sea correcta

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
type ItemType = {
  name: string;
  icon: JSX.Element;
  subItems?: SubItemType[];
};
type SubItemType = {
  title: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano';
  provider: 'ollama' | 'openai';
  api_key?: string;
};
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
  const [isBarOpen, setIsBarOpen] = useState(false);
  const [isItemOpen, setIsItemOpen] = useState(false);
  const { activeModel, configureModel } = useChatHistoryContext(); // Obtener la función sendMessage del contexto

  const [choosedNavItem, setChoosedNavItem] = useState<ItemType | undefined>(
    undefined
  );

  const handleClick = ({
    model,
    provider,
  }: {
    model: 'qwen2.5:3b' | 'gpt-4.1-nano';
    provider: 'ollama' | 'openai';
  }) => {
    if (model === activeModel.model) {
      return;
    }
    const newActiveModel = {
      model: model,
      provider: provider,
    };

    configureModel({
      model: newActiveModel.model,
      provider: newActiveModel.provider,
    });
  };

  return (
    <div
      className={`h-screen bg-gray-900 text-white transition-all duration-400 flex flex-col `}
    >
      <button
        onClick={() => setIsBarOpen(!isBarOpen)}
        className='cursor-pointer p-4 focus:outline-none hover:bg-gray-800 '
      >
        <Menu />
      </button>
      <div className='flex h-full'>
        <nav
          className={`${
            !isBarOpen ? 'w-14' : 'w-32'
          } h-full bg-gray-900 text-white transition-all duration-400 flex-1`}
        >
          {navItems.map((item) => (
            <SidebarItem
              key={item.name}
              item={item}
              isBarOpen={isBarOpen}
              setIsBarOpen={setIsBarOpen}
              isItemOpen={isItemOpen}
              setIsItemOpen={setIsItemOpen}
              setChoosedNavItem={setChoosedNavItem}
              choosedNavItem={choosedNavItem}
            />
          ))}
        </nav>

        <nav
          className={`transition-all duration-500 ${
            !isItemOpen
              ? 'w-0 '
              : 'flex flex-col border-l-stone-50/10 border-l-2 w-32 content-center'
          } `}
        >
          <div className={`${!isItemOpen && 'hidden'} animate-fade-in`}>
            <h1 className='pl-2 mb-2 font-bold'>{choosedNavItem?.name}</h1>
            {choosedNavItem?.subItems?.map((subItem) => (
              <button
                key={subItem.title}
                className={`flex items-center justify-center cursor-pointer w-full py-1 px-2 hover:bg-gray-800 transition-all duration-500 ${
                  activeModel.model === subItem.model && 'bg-gray-800'
                }`}
                type='button'
                onClick={() =>
                  handleClick({
                    model: subItem.model,
                    provider: subItem.provider,
                  })
                }
              >
                {subItem.title}
              </button>
            ))}
          </div>
        </nav>
      </div>
    </div>
  );
}
