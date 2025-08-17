import OpenAI from '@/assets/icons/OpenAI.svg?react';
import Ollama from '@/assets/icons/Ollama.svg?react';
import Anthropic from '@/assets/icons/Anthropic.svg?react';
import Gemini from '@/assets/icons/Gemini.svg?react';
import type { Provider } from '@/types/sidebar';

export const PROVIDER_ICONS: Record<Provider, JSX.Element> = {
  ollama: <Ollama className='w-6 h-6 fill-white' />,
  openai: <OpenAI className='w-6 h-6 fill-white' />,
  anthropic: <Anthropic className='w-6 h-6 fill-white' />, // Temporary, can be replaced with Anthropic icon
  google: <Gemini className='w-6 h-6 fill-white' />, // Temporary, can be replaced with Google icon
};

export const getProviderIcon = (providerName: string): JSX.Element | null => {
  const normalizedName = providerName.toLowerCase() as Provider;
  return PROVIDER_ICONS[normalizedName] || null;
};
