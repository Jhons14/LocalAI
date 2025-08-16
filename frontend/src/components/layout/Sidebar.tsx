import {
  type JSX,
  useEffect,
  useMemo,
  useState,
  memo,
  useCallback,
} from 'react';
import { Menu } from 'lucide-react';

import { SidebarItem } from './SidebarItem';
import OpenAILogo from '../../assets/OpenAILogo.svg?react';
import OllamaLogo from '../../assets/OllamaLogo.svg?react';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { ModelListSkeleton } from '@/components/ui/SkeletonLoader';
import { useToast } from '@/hooks/useToast';
import { useChatApi } from '@/hooks/useChatApi';
import { errorLogger } from '@/utils';

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

export const Sidebar = memo(function Sidebar() {
  const [isItemOpen, setIsItemOpen] = useState(false);
  const [ollamaSubItems, setOllamaSubItems] = useState<Array<SubItemType>>([]);
  const [ollamaSubItemsLoading, setOllamaSubItemsLoading] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  const [selectedSubitemIndex, setSelectedSubitemIndex] = useState<number>();
  const [error, setError] = useState<string | null>(null);
  const { rechargeModel } = useChatHistoryContext();
  const { getOllamaModels } = useChatApi();
  const { error: showError } = useToast();

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
        setError(null);
      };

    const controller = new AbortController();

    const loadOllamaModels = async () => {
      setOllamaSubItemsLoading(true);
      setError(null);

      try {
        const res = await getOllamaModels();

        if (!res) {
          setError('Error obteniendo modelos ollama');
          return;
        }

        const tempOllamaSubItems: SubItemType[] = res['ollama'].map(
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
          const errorMessage =
            'Error getting models, check your ollama connection';
          setError(errorMessage);
          showError('Ollama Connection Error', errorMessage);
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
      setOllamaSubItemsLoading(false);
      setError(null);
    };
  }, [selectedIndex]);

  const handleClick = useCallback(
    ({
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

      rechargeModel(model, provider);
      setSelectedSubitemIndex(index);
    },
    [selectedSubitemIndex]
  );

  const renderOllamaSubItems = useCallback(() => {
    if (error) {
      console.error(error);
      return (
        <div className='text-sm text-red-500 text-center px-2'>
          Fail fetching ollama models
        </div>
      );
    }

    if (ollamaSubItemsLoading) {
      return <ModelListSkeleton />;
    }

    const subItems = choosedNavItem?.subItems || [];

    // Virtual scrolling for large model lists
    if (subItems.length > 20) {
      return (
        <div className='overflow-y-auto max-h-96'>
          <div className='text-xs text-gray-400 px-2 py-1'>
            {subItems.length} models available
          </div>
          {subItems.map((subItem, index) => (
            <button
              key={subItem.title}
              className={`flex items-center justify-center cursor-pointer w-full py-1 px-2 hover:bg-[#555555] transition-all duration-300 text-sm ${
                selectedSubitemIndex === index && 'bg-[#555555]'
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
          ))}
        </div>
      );
    }

    return subItems.map((subItem, index) => (
      <li key={subItem.title}>
        <button
          className={`flex items-center justify-center cursor-pointer w-full py-2 px-2 hover:bg-[#555555] transition-all duration-500 ${
            selectedSubitemIndex === index && 'bg-[#555555]'
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
      </li>
    ));
  }, [
    error,
    ollamaSubItemsLoading,
    choosedNavItem?.subItems,
    selectedSubitemIndex,
    handleClick,
  ]);

  const [render, setRender] = useState(false);

  // Mount when opening; keep mounted while closing so fade-out can play
  useEffect(() => {
    if (isItemOpen) setRender(true);
  }, [isItemOpen]);
  const handleTransitionEnd = () => {
    if (!isItemOpen) setRender(false); // unmount *after* fade/slide finishes
  };

  return (
    <div
      className={`h-screen border-r border-r-[#999999] bg-[#333333] text-white transition-all duration-400 flex flex-col `}
    >
      <button
        onClick={() => {
          setIsItemOpen(!isItemOpen);
        }}
        className='cursor-pointer p-4 border-b border-b-[#999999] focus:outline-none hover:bg-[#555555] transition-all duration-500'
      >
        <Menu />
      </button>
      <div className='flex h-full'>
        <nav
          className={`w-14 h-full bg-[#333333] text-white transition-all duration-400 flex-1 `}
        >
          {navItems.map((item, index) => (
            <SidebarItem
              key={item.name}
              index={index}
              item={item}
              isItemOpen={isItemOpen}
              setIsItemOpen={setIsItemOpen}
              selectedIndex={selectedIndex}
              setSelectedIndex={setSelectedIndex}
            />
          ))}
        </nav>

        <nav
          onTransitionEnd={handleTransitionEnd}
          className={[
            // layout
            'flex flex-col h-full border-l border-l-[#999999] overflow-hidden',
            // animate width + opacity for open/close
            'transition-all duration-300 ease-out',
            isItemOpen
              ? 'w-32 opacity-100'
              : 'w-0 opacity-0 pointer-events-none',
          ].join(' ')}
        >
          <h2 className='overflow-hidden border-b h-11 border-b-[#999999] text-center py-2 font-bold text-xl'>
            <span
              className={[
                'block transition-opacity duration-200',
                isItemOpen ? 'opacity-100' : 'opacity-0',
              ].join(' ')}
            >
              {choosedNavItem?.name}
            </span>
          </h2>

          {/* Fade/slide children too (optional) */}
          <ul
            className={[
              'overflow-hidden transition-opacity duration-200',
              isItemOpen ? 'opacity-100' : 'opacity-0',
            ].join(' ')}
          >
            {renderOllamaSubItems()}
          </ul>
        </nav>
      </div>
    </div>
  );
});
