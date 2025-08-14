import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { Eye, EyeOff, History } from 'lucide-react';
import { useState, memo, useCallback, useMemo } from 'react';
import { LoadingButton, ConnectionStatus } from '@/components/ui/LoadingStates';
import { useToast } from '@/hooks/useToast';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useValidation } from '@/hooks/useValidation';
import { ChatHistoryManager } from '@/components/chat/ChatHistoryManager';
import { ToolsList } from '../ui/ToolsList';

export const TopNavBar = memo(function TopNavBar() {
  const {
    activeModel,
    isModelConnected,
    tempApiKey,
    setTempApiKey,
    configureModel,
  } = useChatHistoryContext();
  const { success, error } = useToast();
  const { isMobile } = useMobileFirst();
  const [showHistoryManager, setShowHistoryManager] = useState<boolean>(false);
  const [isModelLoading, setIsModelLoading] = useState<boolean>(false);

  const deleteKey = useCallback(() => {
    setTempApiKey('');
  }, [setTempApiKey]);

  return (
    <div
      className={`grid grid-cols-[1fr_2fr_1fr_1fr] mb-2 ${
        isMobile
          ? 'flex-col gap-2 p-3'
          : 'flex-row justify-between items-center gap-4 px-8'
      } border-b border-[#999999] ${isMobile ? 'min-h-[100px]' : 'h-20'}`}
    >
      <h1
        className={`${
          isMobile ? 'text-lg text-center' : 'text-xl'
        } font-bold w-fit ${isMobile ? 'w-full' : 'min-w-max'}`}
      >
        {activeModel?.model || 'Select a model...'}
      </h1>

      {!tempApiKey && activeModel ? (
        <ApiKeyInput provider={activeModel.provider} />
      ) : (
        <span className={`${isMobile ? 'text-center text-sm' : 'text-base'}`}>
          Api key saved
        </span>
      )}
      <button
        onClick={() => setShowHistoryManager(true)}
        className={`flex items-center gap-2 px-3 py-2 border cursor-pointer border-[#999999] rounded hover:bg-[#555555] hover:text-white transition-all duration-200] keyboard-navigation ${
          isMobile ? 'w-full justify-center' : ''
        }`}
        aria-label='Open chat history manager'
      >
        <History size={16} />
        {isMobile ? 'History' : 'Chat History'}
      </button>
      {activeModel?.model && <ToolsList model={activeModel.model} />}

      <ChatHistoryManager
        isOpen={showHistoryManager}
        onClose={() => setShowHistoryManager(false)}
      />
    </div>
  );
});

const ApiKeyInput = memo(function ApiKeyInput({
  provider,
}: {
  provider: string;
}) {
  if (provider !== 'openai') return <div></div>;
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTempApiKey } = useChatHistoryContext();
  const { validateField, getFieldError, hasFieldError, clearValidation } =
    useValidation();
  const { error: showError, success: showSuccess } = useToast();

  const saveKeys = useCallback(async () => {
    setLoading(true);

    // Validate the API key
    const validation = validateField('apiKey', apiKey);

    if (!validation.isValid) {
      showError('Invalid API Key', validation.errors[0]);
      setLoading(false);
      return;
    }

    try {
      // Use sanitized value if available
      const sanitizedApiKey = validation.sanitizedValue || apiKey;
      setTempApiKey(sanitizedApiKey);
      showSuccess('API Key Saved', 'Your API key has been securely saved.');
      clearValidation('apiKey');
    } catch (error) {
      showError('Save Failed', 'Failed to save API key. Please try again.');
    }

    setLoading(false);
  }, [
    apiKey,
    setTempApiKey,
    validateField,
    showError,
    showSuccess,
    clearValidation,
  ]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        saveKeys();
        setApiKey('');
        (e.currentTarget as HTMLInputElement).blur();
      }
    },
    [saveKeys]
  );

  return (
    <div className='relative flex w-full items-center justify-center'>
      {!loading ? (
        <div className='relative flex py-2 items-center w-full'>
          <input
            type={show ? 'text' : 'password'}
            id='apiKey'
            name='apiKey'
            placeholder={provider + ' API Key'}
            autoComplete='off'
            className={`w-full pr-10 px-4 py-2 border ${
              hasFieldError('apiKey') ? 'border-red-500' : 'border-[#999999]'
            }  rounded-lg shadow-sm keyboard-navigation`}
            value={apiKey}
            onChange={(e) => {
              setApiKey(e.target.value);
              if (hasFieldError('apiKey')) {
                clearValidation('apiKey');
              }
            }}
            onKeyDown={handleKeyPress}
            aria-invalid={hasFieldError('apiKey')}
            aria-describedby={
              hasFieldError('apiKey') ? 'apikey-error' : undefined
            }
          />
          <button
            type='button'
            onClick={() => setShow((prev) => !prev)}
            className='cursor-pointer absolute right-3 text-gray-500 hover:text-blue-600'
          >
            {show ? (
              <EyeOff className='w-5 h-5' />
            ) : (
              <Eye className='w-5 h-5' />
            )}
          </button>
        </div>
      ) : (
        <div className='loader'></div>
      )}

      {hasFieldError('apiKey') && (
        <div
          id='apikey-error'
          className='flex w-40 self-end pb-4 text-red-500 shadow-xl text-sm'
          role='alert'
        >
          {getFieldError('apiKey')}
        </div>
      )}
    </div>
  );
});
