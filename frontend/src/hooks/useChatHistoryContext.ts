import { useContext } from 'react';

import { ChatHistoryContext } from '../context/ChatHistoryContext';

export function useChatHistoryContext() {
  const context = useContext(ChatHistoryContext);

  if (!context) {
    throw new Error('useChatHistoryContext must be used within a MyProvider');
  }
  return context;
}
