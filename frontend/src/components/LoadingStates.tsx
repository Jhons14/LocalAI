import { memo } from 'react';
import { LoadingSpinner } from './SkeletonLoader';

interface LoadingButtonProps {
  isLoading: boolean;
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  type?: 'button' | 'submit' | 'reset';
}

export const LoadingButton = memo(function LoadingButton({
  isLoading,
  children,
  onClick,
  disabled,
  className = '',
  type = 'button'
}: LoadingButtonProps) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled || isLoading}
      className={`
        relative flex items-center justify-center gap-2 px-4 py-2 rounded-lg
        transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500
        disabled:opacity-50 disabled:cursor-not-allowed
        ${isLoading ? 'cursor-wait' : 'cursor-pointer'}
        ${className}
      `}
    >
      {isLoading && (
        <LoadingSpinner size="sm" className="text-current" />
      )}
      <span className={isLoading ? 'opacity-75' : 'opacity-100'}>
        {children}
      </span>
    </button>
  );
});

interface LoadingOverlayProps {
  isLoading: boolean;
  message?: string;
  children: React.ReactNode;
}

export const LoadingOverlay = memo(function LoadingOverlay({
  isLoading,
  message = 'Loading...',
  children
}: LoadingOverlayProps) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-10">
          <div className="flex flex-col items-center space-y-2">
            <LoadingSpinner size="lg" />
            <p className="text-sm text-gray-600">{message}</p>
          </div>
        </div>
      )}
    </div>
  );
});

interface InlineLoadingProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const InlineLoading = memo(function InlineLoading({
  message = 'Loading...',
  size = 'md'
}: InlineLoadingProps) {
  return (
    <div className="flex items-center space-x-2 text-gray-600">
      <LoadingSpinner size={size} />
      <span className="text-sm">{message}</span>
    </div>
  );
});

export const TypingIndicator = memo(function TypingIndicator() {
  return (
    <div className="flex items-center space-x-1 text-gray-500">
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
        <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      </div>
      <span className="text-sm ml-2">AI is thinking...</span>
    </div>
  );
});

export const ConnectionStatus = memo(function ConnectionStatus({
  isConnected,
  isConnecting,
  modelName
}: {
  isConnected: boolean;
  isConnecting: boolean;
  modelName?: string;
}) {
  if (isConnecting) {
    return (
      <div className="flex items-center space-x-2 text-yellow-600">
        <LoadingSpinner size="sm" />
        <span className="text-sm">Connecting to {modelName}...</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center space-x-2 ${isConnected ? 'text-green-600' : 'text-red-600'}`}>
      <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
      <span className="text-sm">
        {isConnected ? `Connected to ${modelName}` : 'Disconnected'}
      </span>
    </div>
  );
});