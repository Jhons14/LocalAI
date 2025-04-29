import { ChatOutput } from './ChatOutput';
import { useChatHistoryContext } from '../context/ChatHistoryContext'; // Asegúrate de que la ruta sea correcta
import { ChatInput } from './ChatInput';

export function Chat() {
  const { activeModel, configureModel, isModelConnected } =
    useChatHistoryContext();

  const handleModelChange = () => {
    configureModel({
      model: activeModel.model,
      provider: activeModel.provider,
    });
  };

  return (
    <div className='flex flex-col h-screen w-full relative '>
      {!!activeModel.model && (
        <div className='flex justify-between items-center p-4 border-b border-gray-500'>
          <h1 className='text-xl font-bold'>{activeModel.model}</h1>
          <button
            className={`py-2 px-4 w-[140px] rounded-sm ${
              activeModel
                ? 'bg-green-700 text-white cursor-default pointer-events-none'
                : 'cursor-pointer bg-gray-500 hover:bg-green-600'
            }`}
            type='button'
            onClick={() => handleModelChange()}
          >
            {!isModelConnected ? 'Conectando...' : 'Conectado'}
          </button>
        </div>
      )}
      <ChatOutput thread_id={activeModel.thread_id} />
      <ChatInput thread_id={activeModel.thread_id} />
    </div>
  );
}
