import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { Eye, EyeOff } from 'lucide-react';
import { useState, memo, useCallback, useMemo } from 'react';

export const TopNavBar = memo(function TopNavBar() {
  // Obtener el contexto de ChatHistoryContext
  const {
    activeModel,
    isModelConnected,
    tempApiKey,
    setTempApiKey,
    configureModel,
  } = useChatHistoryContext();
  const [showApikeyMenu, setShowApikeyMenu] = useState<boolean>(false);
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const [isModelLoading, setIsModelLoading] = useState<boolean>(false);
  
  const deleteKey = useCallback(() => {
    setTempApiKey('');
  }, [setTempApiKey]);

  const handleConnect = useCallback(async () => {
    if (!activeModel) {
      alert('Please select a model first.');
      return;
    }
    setIsModelLoading(true);

    try {
      await configureModel({
        model: activeModel.model,
        provider: activeModel.provider,
      });
    } catch (error) {
      console.error('Error connecting to model:', error);
    }

    setIsModelLoading(false);
  }, [activeModel, configureModel]);

  const renderConnectButton = useMemo(() => {
    if (!!isModelConnected && !isModelLoading) {
      return <span className='text-2xl'>Conectado</span>;
    }
    if (isModelLoading) {
      return <div className='loader'></div>;
    }
    if (!isModelConnected && !isModelLoading && activeModel) {
      return (
        <div className='text-2xl'>
          <button
            className='cursor-pointer rounded-lg bg-gray-500 px-4 py-2 text-white hover:bg-blue-600'
            onClick={handleConnect}
          >
            Conectar
          </button>
        </div>
      );
    }
  }, [isModelConnected, isModelLoading, activeModel, handleConnect]);

  return (
    <div className='flex justify-between items-center gap-4 px-8 border-b border-gray-500 h-20'>
      <h1 className='text-xl font-bold w-fit min-w-max'>
        {activeModel?.model || 'Select a model to start...'}
      </h1>

      {activeModel?.provider === 'openai' &&
        (!tempApiKey ? (
          <ApiKeyInput
            model={activeModel.model}
            provider={activeModel.provider}
          />
        ) : (
          <span>Api key saved</span>
        ))}
      {renderConnectButton}
    </div>
  );
});

const ApiKeyInput = memo(function ApiKeyInput({ model, provider }: { model: string; provider: string }) {
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [inputError, setInputError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setTempApiKey } = useChatHistoryContext();

  const saveKeys = useCallback(async () => {
    setInputError('');
    setLoading(true);
    if (!apiKey) {
      setInputError('API Key is required');
      setLoading(false);
      return;
    }
    setTempApiKey(apiKey);

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
  }, [apiKey, setTempApiKey]);

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
                !inputError ? 'border-gray-300' : 'border-red-500'
              } rounded-lg shadow-sm focus:outline-none focus:ring focus:border-blue-500`}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              onKeyDown={handleKeyPress}
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

      {inputError && (
        <p className='flex w-40 self-end pb-4 text-red-500 shadow-xl '>
          {inputError}
        </p>
      )}
    </div>
  );
});
