import { ErrorBoundary } from './ErrorBoundary';
import { type ReactNode } from 'react';

interface ChatErrorBoundaryProps {
  children: ReactNode;
}

export function ChatErrorBoundary({ children }: ChatErrorBoundaryProps) {
  const handleError = (error: Error) => {
    // Log to external service if needed
    console.error('Chat error:', error);
  };

  const fallback = (
    <div className='flex flex-col items-center justify-center p-8 text-center bg-gray-50 rounded-lg'>
      <div className='text-red-500 mb-4'>
        <svg
          className='w-12 h-12 mx-auto'
          fill='none'
          stroke='currentColor'
          viewBox='0 0 24 24'
        >
          <path
            strokeLinecap='round'
            strokeLinejoin='round'
            strokeWidth={2}
            d='M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
          />
        </svg>
      </div>
      <h3 className='text-lg font-semibold text-gray-900 mb-2'>Chat Error</h3>
      <p className='text-gray-600 mb-4'>
        There was an error with the chat component. Please try refreshing the
        page.
      </p>
      <button
        onClick={() => window.location.reload()}
        className='px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600'
      >
        Refresh Page
      </button>
    </div>
  );

  return (
    <ErrorBoundary fallback={fallback} onError={handleError}>
      {children}
    </ErrorBoundary>
  );
}
