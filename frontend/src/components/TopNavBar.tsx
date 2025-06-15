import { useChatHistoryContext } from '@/hooks/useChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { Eye, EyeOff } from 'lucide-react'; // Puedes usar cualquier ícono SVG
import { useState } from 'react';

export function TopNavBar() {
  // Obtener el contexto de ChatHistoryContext
  const { activeModel, isModelConnected, isApiKeySaved, configureModel } =
    useChatHistoryContext();
  const [showApikeyMenu, setShowApikeyMenu] = useState<boolean>(false);
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;

  return (
    <div className='flex justify-between items-center gap-4 px-8 border-b border-gray-500 h-20'>
      <h1 className='text-xl font-bold w-fit min-w-max'>
        {activeModel.model || 'Select a model to start...'}
      </h1>

      {activeModel.provider === 'openai' &&
        (!isApiKeySaved ? (
          <ApiKeyInput
            model={activeModel.model}
            provider={activeModel.provider}
          />
        ) : (
          <div
            className={`flex relative cursor-pointer`}
            onPointerOver={() => setShowApikeyMenu(true)}
            onPointerOut={() => setShowApikeyMenu(false)}
            onClick={() => setShowApikeyMenu(false)}
          >
            Api key saved
            <div
              className={`text-sm font-light px-2 py-2 hover:scale-105 transition-all duration-200 rounded-md bg-gray-700 top-6 right-[-40px] ${
                showApikeyMenu ? 'absolute' : 'hidden'
              }`}
              onClick={async () => {
                await fetch(
                  `${BACKEND_URL}/keys/${activeModel.provider}/${activeModel.model}`,
                  {
                    method: 'delete',
                    headers: {
                      'Content-Type': 'application/json',
                    },
                  }
                );
                configureModel({
                  model: activeModel.model,
                  provider: activeModel.provider,
                });
              }}
            >
              Delete ApiKey
            </div>
          </div>
        ))}
      <span className='text-2xl'>{!!isModelConnected && 'Conectado'}</span>
    </div>
  );
}

function ApiKeyInput({ model, provider }: { model: string; provider: string }) {
  const BACKEND_URL = import.meta.env.PUBLIC_BACKEND_URL;
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [inputError, setInputError] = useState('');
  const [loading, setLoading] = useState(false);
  const { setIsApiKeySaved } = useChatHistoryContext();

  const saveKeys = async () => {
    setInputError('');
    setLoading(true);
    try {
      const res = await fetch(BACKEND_URL + '/keys/validate-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ apiKey }),
      });

      if (!res.ok) {
        const jsonRes = await res.json();
        setInputError('Invalid ' + provider + ' apikey');
        throw new Error(jsonRes.detail);
      }

      const POSTKeysRes = await fetch(BACKEND_URL + '/keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model, provider, api_key: apiKey }),
      });
      if (!POSTKeysRes.ok) {
        throw new Error('Network response was not ok');
      }

      const GETkeysRes = await fetch(BACKEND_URL + '/keys', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!GETkeysRes.ok) {
        throw new Error('Network response was not ok');
      }
      const keys = await GETkeysRes.json();

      setIsApiKeySaved(provider in keys ? true : false);
    } catch (error) {
      console.error('Error:', error);
    }
    setLoading(false);
  };

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
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  // Aquí puedes manejar el evento de enviar la API Key
                  saveKeys();
                  setApiKey(''); // Limpiar el campo después de enviarq
                  e.currentTarget.blur(); // Volver a enfocar el input
                }
              }}
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
}
