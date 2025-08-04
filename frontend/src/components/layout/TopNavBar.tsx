import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { Eye, EyeOff, History } from 'lucide-react';
import { useState, memo, useCallback, useMemo } from 'react';
import { LoadingButton, ConnectionStatus } from '@/components/ui/LoadingStates';
import { useToast } from '@/hooks/useToast';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useValidation } from '@/hooks/useValidation';
import { ChatHistoryManager } from '@/components/chat/ChatHistoryManager';

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
  const [showApikeyMenu, setShowApikeyMenu] = useState<boolean>(false);
  const [showHistoryManager, setShowHistoryManager] = useState<boolean>(false);
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const [isModelLoading, setIsModelLoading] = useState<boolean>(false);
  
  const deleteKey = useCallback(() => {
    setTempApiKey('');
  }, [setTempApiKey]);

  const handleConnect = useCallback(async () => {
    if (!activeModel) {
      error('No Model Selected', 'Please select a model first.');
      return;
    }
    setIsModelLoading(true);

    try {
      await configureModel({
        model: activeModel.model,
        provider: activeModel.provider,
      });
      success('Connected!', `Successfully connected to ${activeModel.model}`);
    } catch (err) {
      console.error('Error connecting to model:', err);
      error('Connection Failed', err instanceof Error ? err.message : 'Failed to connect to model');
    }

    setIsModelLoading(false);
  }, [activeModel, configureModel, success, error]);

  const renderConnectButton = useMemo(() => {
    if (!activeModel) {
      return <span className='text-sm text-gray-500'>Select a model to start</span>;
    }

    if (isModelConnected && !isModelLoading) {
      return (
        <ConnectionStatus 
          isConnected={true} 
          isConnecting={false} 
          modelName={activeModel.model} 
        />
      );
    }

    return (
      <LoadingButton
        isLoading={isModelLoading}
        onClick={handleConnect}
        className='bg-blue-500 text-white hover:bg-blue-600'
      >
        {isModelLoading ? 'Connecting...' : 'Connect'}
      </LoadingButton>
    );
  }, [isModelConnected, isModelLoading, activeModel, handleConnect]);

  return (
    <div className={`flex ${isMobile ? 'flex-col gap-2 p-3' : 'flex-row justify-between items-center gap-4 px-8'} border-b border-gray-500 ${isMobile ? 'min-h-[100px]' : 'h-20'}`}>
      <h1 className={`${isMobile ? 'text-lg text-center' : 'text-xl'} font-bold w-fit ${isMobile ? 'w-full' : 'min-w-max'}`}>
        {activeModel?.model || 'Select a model...'}
      </h1>

      <div className={`flex ${isMobile ? 'flex-col gap-2 w-full' : 'flex-row items-center gap-4'}`}>
        {activeModel?.provider === 'openai' &&
          (!tempApiKey ? (
            <ApiKeyInput
              model={activeModel.model}
              provider={activeModel.provider}
            />
          ) : (
            <span className={`${isMobile ? 'text-center text-sm' : 'text-base'}`}>Api key saved</span>
          ))}
        <button
          onClick={() => setShowHistoryManager(true)}
          className={`flex items-center gap-2 px-3 py-2 border border-gray-300 rounded hover:bg-gray-50 keyboard-navigation ${isMobile ? 'w-full justify-center' : ''}`}
          aria-label="Open chat history manager"
        >
          <History size={16} />
          {isMobile ? 'History' : 'Chat History'}
        </button>
        
        <div className={`${isMobile ? 'w-full flex justify-center' : ''}`}>
          {renderConnectButton}
        </div>
      </div>
      
      <ChatHistoryManager 
        isOpen={showHistoryManager}
        onClose={() => setShowHistoryManager(false)}
      />
    </div>
  );
});

const ApiKeyInput = memo(function ApiKeyInput({ model, provider }: { model: string; provider: string }) {
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTempApiKey } = useChatHistoryContext();
  const { validateField, getFieldError, hasFieldError, clearValidation } = useValidation();
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

    // try {
    //   const res = await fetch(BACKEND_URL + '/keys/validate-keys', {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({ apiKey }),
    //   });

    //   if (!res.ok) {
    //     const jsonRes = await res.json();
    //     setInputError('Invalid ' + provider + ' apikey');
    //     throw new Error(jsonRes.detail);
    //   }

    //   const POSTKeysRes = await fetch(BACKEND_URL + '/keys', {
    //     method: 'POST',
    //     headers: {
    //       'Content-Type': 'application/json',
    //     },
    //     body: JSON.stringify({ model, provider, api_key: apiKey }),
    //   });
    //   if (!POSTKeysRes.ok) {
    //     throw new Error('Network response was not ok');
    //   }

    //   const GETkeysRes = await fetch(BACKEND_URL + '/keys', {
    //     method: 'GET',
    //     headers: {
    //       'Content-Type': 'application/json',
    //     },
    //   });

    //   if (!GETkeysRes.ok) {
    //     throw new Error('Network response was not ok');
    //   }
    //   const keys = await GETkeysRes.json();

    //   setIsApiKeySaved(provider in keys ? true : false);
    // } catch (error) {
    //   console.error('Error:', error);
    // }
    setLoading(false);
  }, [apiKey, setTempApiKey, validateField, showError, showSuccess, clearValidation]);

  const handleKeyPress = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      saveKeys();
      setApiKey('');
      e.currentTarget.blur();
    }
  }, [saveKeys]);

  return (
    <div className='relative flex w-full items-center justify-center gap-2'>
      {!loading ? (
        <div className='flex flex-col py-2'>
          <label
            htmlFor='apiKey'
            className='mb-1 text-nowrap text-sm font-thin text-gray-300'
          >
            OpenAI API Key
          </label>

          <div className='relative flex items-center'>
            <input
              type={show ? 'text' : 'password'}
              id='apiKey'
              name='apiKey'
              placeholder='sk-...'
              autoComplete='off'
              className={`w-full pr-10 px-4 py-2 border ${
                hasFieldError('apiKey') ? 'border-red-500' : 'border-gray-300'
              } rounded-lg shadow-sm focus:outline-none focus:ring focus:border-blue-500 keyboard-navigation`}
              value={apiKey}
              onChange={(e) => {
                setApiKey(e.target.value);
                if (hasFieldError('apiKey')) {
                  clearValidation('apiKey');
                }
              }}
              onKeyDown={handleKeyPress}
              aria-invalid={hasFieldError('apiKey')}
              aria-describedby={hasFieldError('apiKey') ? 'apikey-error' : undefined}
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
        </div>
      ) : (
        <div className='loader'></div>
      )}

      {hasFieldError('apiKey') && (
        <div id="apikey-error" className='flex w-40 self-end pb-4 text-red-500 shadow-xl text-sm' role="alert">
          {getFieldError('apiKey')}
        </div>
      )}
    </div>
  );
});
