import { useChatHistoryContext } from '@/context/ChatHistoryContext';
import { Eye, EyeOff } from 'lucide-react'; // Puedes usar cualquier ícono SVG

import { useState } from 'react';
export function TopNavBar() {
  // Obtener el contexto de ChatHistoryContext
  const { activeModel, isModelConnected } = useChatHistoryContext();

  return (
    <div className='flex justify-between items-center gap-4 p-4 border-b border-gray-500 '>
      <h1 className='text-xl font-bold'>{activeModel.model}</h1>

      {activeModel.provider === 'openai' && (
        <ApiKeyInput
          model={activeModel.model}
          provider={activeModel.provider}
        />
      )}
      <button
        className={`py-2 px-4 w-[140px] rounded-sm ${
          activeModel
            ? 'bg-green-700 text-white cursor-default pointer-events-none'
            : 'cursor-pointer bg-gray-500 hover:bg-green-600'
        }`}
        type='button'
      >
        {!isModelConnected ? 'Conectando...' : 'Conectado'}
      </button>
    </div>
  );
}

function ApiKeyInput({ model, provider }: { model: string; provider: string }) {
  const [show, setShow] = useState(false);
  const [apiKey, setApiKey] = useState('');
  return (
    <div className='relative w-full max-w-md'>
      <label
        htmlFor='apiKey'
        className='block mb-1 text-sm font-bold text-gray-300'
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
          className='w-full pr-10 px-4 py-2 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring focus:border-blue-500'
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              // Aquí puedes manejar el evento de enviar la API Key
              console.log(' Key:', apiKey);
              fetch('http://127.0.0.1:8000/keys', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model, provider, api_key: apiKey }),
              })
                .then((response) => {
                  if (!response.ok) {
                    throw new Error('Network response was not ok');
                  }
                  return response.json();
                })
                .then((data) => {
                  console.log('Success:', data);
                })
                .catch((error) => {
                  console.error('Error:', error);
                });
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
          {show ? <EyeOff className='w-5 h-5' /> : <Eye className='w-5 h-5' />}
        </button>
      </div>
    </div>
  );
}
