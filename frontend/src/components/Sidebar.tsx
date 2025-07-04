import { type JSX, use, useEffect, useMemo, useState } from 'react';
import { Menu } from 'lucide-react';
import { SidebarItem } from './SidebarItem';
import OpenAILogo from '../assets/OpenAILogo.svg?react';
import OllamaLogo from '../assets/OllamaLogo.svg?react';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { v4 as uuid } from 'uuid';

type NavType = {
  name: string;
  icon: JSX.Element;
  subItems?: SubItemType[];
}[];

type SubItemType = {
  title: string;
  model: 'qwen2.5:3b' | 'gpt-4.1-nano';
  provider: 'ollama' | 'openai';
  api_key?: string;
};

export function Sidebar() {
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL; // Asegúrate de que la ruta sea correcta

  const [isBarOpen, setIsBarOpen] = useState(false);
  const [isItemOpen, setIsItemOpen] = useState(false);
  const [ollamaSubItems, setOllamaSubItems] = useState<Array<SubItemType>>([]); // Obtener la función sendMessage del contexto
  const [ollamaSubItemsLoading, setOllamaSubItemsLoading] = useState(false); // Obtener la función sendMessage del contexto
  const [selectedIndex, setSelectedIndex] = useState<number>();
  const [selectedSubitemIndex, setSelectedSubitemIndex] = useState<number>();
  const [error, setError] = useState<string | null>(null);
  const { rechargeModel, setIsModelConnected } = useChatHistoryContext(); // Obtener la función sendMessage del contexto

  const navItems = useMemo<NavType>(
    () => [
      {
        name: 'Ollama',
        icon: <OllamaLogo className='w-6 h-6  fill-white' />,
        subItems: ollamaSubItems,
      },
      {
        name: 'OpenAI',
        icon: <OpenAILogo className='w-6 h-6 fill-white' />,
        subItems: [
          { title: 'gpt-4.1-nano', model: 'gpt-4.1-nano', provider: 'openai' },
        ],
      },
    ],
    [ollamaSubItems]
  );

  const choosedNavItem = navItems[selectedIndex];

  useEffect(() => {
    if (choosedNavItem?.name !== 'Ollama')
      return () => {
        setSelectedSubitemIndex(undefined); // Resetea el índice del subitem seleccionado
        setOllamaSubItems([]); // limpio para evitar mostrar datos viejos
        setOllamaSubItemsLoading(false);
        setError(null);
        setIsModelConnected(false);
      };

    const controller = new AbortController();
    const signal = controller.signal;

    const loadOllamaModels = async () => {
      setOllamaSubItemsLoading(true);
      setError(null);

      try {
        const res = await fetch(BACKEND_URL + '/getModels', { signal });

        if (!res.ok) {
          setError('Error obteniendo modelos ollama');
          return;
        }

        const parsedRes = await res.json();

        const tempOllamaSubItems: SubItemType[] = parsedRes.map(
          (model: string) => ({
            title: model,
            model: model,
            provider: 'ollama',
          })
        );

        setOllamaSubItems(tempOllamaSubItems);
      } catch (err: any) {
        if (err.name !== 'AbortError') {
          console.error('Error fetching models from Ollama:', err);
          setError('Error getting models, check your ollama connection');
        }
      } finally {
        setOllamaSubItemsLoading(false);
      }
    };

    loadOllamaModels();

    // Cleanup: cancela la petición si cambia `selectedIndex` o se desmonta el componente
    return () => {
      controller.abort();
      setSelectedSubitemIndex(undefined); // Resetea el índice del subitem seleccionado
      setOllamaSubItems([]); // limpio para evitar mostrar datos viejos
      setOllamaSubItemsLoading(false);
      setError(null);
      setIsModelConnected(false);
    };
  }, [selectedIndex]);

  const handleClick = ({
    index,
    model,
    provider,
  }: {
    index: number;
    model: 'qwen2.5:3b' | 'gpt-4.1-nano';
    provider: 'ollama' | 'openai';
  }) => {
    if (index === selectedSubitemIndex) {
      return;
    }

    // if (provider === 'ollama') {
    //   configureModel({
    //     model: model,
    //     provider: provider,
    //     connectModel: true,
    //   }); // Configurar el modelo activo
    // }
    rechargeModel(model, provider);
    setSelectedSubitemIndex(index);
  };

  const renderOllamaSubItems = () => {
    if (error) {
      return (
        <div className='text-sm text-red-500 text-center px-2'>{error}</div>
      );
    }

    if (ollamaSubItemsLoading) {
      return (
        <div className='flex items-center h-full justify-center'>
          <span className='loader'></span>
        </div>
      );
    }

    return choosedNavItem?.subItems.map((subItem, index) => (
      <button
        key={subItem.title}
        className={`flex items-center justify-center cursor-pointer w-full py-1 px-2 hover:bg-gray-800 transition-all duration-500 ${
          selectedSubitemIndex === index && 'bg-gray-800'
        }`}
        type='button'
        onClick={() =>
          handleClick({
            index: index,
            model: subItem.model,
            provider: subItem.provider,
          })
        }
      >
        {subItem.title}
      </button>
    ));
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
          {navItems.map((item, index) => (
            <SidebarItem
              key={item.name}
              index={index}
              item={item}
              isBarOpen={isBarOpen}
              setIsBarOpen={setIsBarOpen}
              isItemOpen={isItemOpen}
              setIsItemOpen={setIsItemOpen}
              selectedIndex={selectedIndex}
              setSelectedIndex={setSelectedIndex}
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
          <div className={`${!isItemOpen && 'hidden'} h-full animate-fade-in`}>
            <h1 className='pl-2 mb-2 font-bold text-xl'>
              {choosedNavItem?.name}
            </h1>
            {renderOllamaSubItems()}
          </div>
        </nav>
      </div>
    </div>
  );
}
