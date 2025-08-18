import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { Key, History } from 'lucide-react';
import { useState, memo } from 'react';
import { useMobileFirst } from '@/hooks/useResponsive';
import { ChatHistoryManager } from '@/components/chat/ChatHistoryManager';
import { ApiKeyModal } from '@/components/ui/ApiKeyModal';
import { Tools } from '../ui/Tools';

export const TopNavBar = memo(function TopNavBar() {
  const { activeModel, tempApiKey, clear } = useChatHistoryContext();
  const { isMobile } = useMobileFirst();
  const [showHistoryManager, setShowHistoryManager] = useState<boolean>(false);
  const [showApiKeyModal, setShowApiKeyModal] = useState<boolean>(false);

  return (
    <div
      className={`grid grid-cols-2 mb-2 p-3 ${
        isMobile ? 'flex-col gap-2 p-3' : 'flex-row items-center gap-4'
      } border-b border-[#999999] ${
        isMobile ? 'min-h-[100px]' : 'h-20 justify-between'
      }`}
    >
      <div className={`flex items-center gap-6  ${!isMobile && 'ml-4'}`}>
        <h1
          className={`${
            isMobile ? 'text-lg text-left' : 'text-xl'
          } font-bold w-fit  ${isMobile ? 'w-full' : 'min-w-max'}`}
        >
          {activeModel?.model || 'Select a model...'}
        </h1>
      </div>
      <div className={`flex justify-end gap-4 ${!isMobile && 'h-10'}`}>
        {activeModel && activeModel.provider !== 'ollama' && (
          <button
            onClick={() => setShowApiKeyModal(true)}
            className={`flex items-center ${
              tempApiKey && ''
            } gap-2 p-2 border cursor-pointer  ${
              tempApiKey ? 'border-green-700' : 'border-[#999999]'
            } rounded hover:bg-[#555555] hover:text-white transition-all duration-200 keyboard-navigation ${
              isMobile ? 'w-full justify-center text-sm' : 'justify-center'
            }`}
            aria-label={`Set ${activeModel.provider} API key`}
          >
            <Key size={24} className={`${tempApiKey && 'text-green-700'}`} />
          </button>
        )}
        <button
          onClick={() => setShowHistoryManager(true)}
          className={`flex items-center gap-2 p-2 border cursor-pointer border-[#999999] rounded hover:bg-[#555555] hover:text-white transition-all duration-200 keyboard-navigation ${
            isMobile ? 'w-full justify-center' : 'justify-self-end'
          }`}
          aria-label='Open chat history manager'
        >
          <History />
        </button>
        <Tools model={activeModel} />
      </div>
      <ChatHistoryManager
        isOpen={showHistoryManager}
        onClose={() => setShowHistoryManager(false)}
        onClearAll={clear}
      />
      {activeModel && (
        <ApiKeyModal
          isOpen={showApiKeyModal}
          onClose={() => setShowApiKeyModal(false)}
          provider={activeModel.provider}
        />
      )}
    </div>
  );
});
