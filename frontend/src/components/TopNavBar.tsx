import { useChatHistoryContext } from '@/hooks/useChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { Eye, EyeOff } from 'lucide-react'; // Puedes usar cualquier ícono SVG
import { useState } from 'react';

export function TopNavBar() {
  // Obtener el contexto de ChatHistoryContext
  const { activeModel, isModelConnected, isApiKeySaved, configureModel } =
    useChatHistoryContext();
  const [showApikeyMenu, setShowApikeyMenu] = useState<boolean>(false);

  return (
    <div className='flex justify-between items-center gap-4 py-1 px-8 border-b border-gray-500 h-max '>
      <h1 className='text-xl font-bold'>
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
                  `http://127.0.0.1:8000/keys/${activeModel.provider}/${activeModel.model}`,
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
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [inputError, setInputError] = useState('');
  const { setIsApiKeySaved } = useChatHistoryContext();

  const saveKeys = () => {
    fetch('http://127.0.0.1:8000/keys/validate-keys', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ apiKey }),
    }).then(async (res) => {
      if (!res.ok) {
        const jsonRes = await res.json();
        setInputError('Invalid ' + provider + ' apikey');
        throw new Error(jsonRes.detail);
      }
      fetch('http://127.0.0.1:8000/keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ model, provider, api_key: apiKey }),
      })
        .then(async (response) => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          await fetch('http://127.0.0.1:8000/keys', {
            method: 'get',
            headers: {
              'Content-Type': 'application/json',
            },
          }).then(async (res) => {
            if (!res.ok) {
              throw new Error('Network response was not ok');
            }
            const keys = await res.json();

            setIsApiKeySaved(provider in keys ? true : false);
          });
          return response.json();
        })
        .then((data) => {
          console.log('Success:', data);
        })
        .catch((error) => {
          console.error('Error:', error);
        });
    });
  };

  return (
    <div className='relative flex w-full items-center justify-center gap-2'>
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
      <p className='flex w-40 self-end pb-4 text-red-500 shadow-xl '>
        {inputError}
      </p>
    </div>
  );
}
