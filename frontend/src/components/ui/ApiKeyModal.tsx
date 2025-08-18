import { useState, memo, useCallback, useEffect } from 'react';
import { Eye, EyeOff, Key, X } from 'lucide-react';
import { useToast } from '@/hooks/useToast';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useValidation } from '@/hooks/useValidation';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { useEscapeKey } from '@/hooks/useKeyboard';

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  provider: string;
}

export const ApiKeyModal = memo(function ApiKeyModal({
  isOpen,
  onClose,
  provider,
}: ApiKeyModalProps) {
  const [show, setShow] = useState(false);
  const { setTempApiKey, tempApiKey } = useChatHistoryContext();
  const [apiKey, setApiKey] = useState(tempApiKey || '');

  const [loading, setLoading] = useState(false);
  const { isMobile } = useMobileFirst();
  const { validateField, getFieldError, hasFieldError, clearValidation } =
    useValidation();
  const { error: showError, success: showSuccess } = useToast();
  // Add this useEffect to sync with tempApiKey changes
  useEffect(() => {
    setApiKey(tempApiKey || '');
  }, [tempApiKey]);
  // Close on Escape key
  useEscapeKey(() => {
    if (isOpen) onClose();
  });

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
      setApiKey('');
      onClose();
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
    onClose,
  ]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        saveKeys();
      }
    },
    [saveKeys]
  );

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
      <div
        className={`bg-white rounded-lg shadow-xl ${
          isMobile ? 'w-full mx-4' : 'w-full max-w-md'
        } flex flex-col`}
      >
        {/* Header */}
        <div className='flex justify-between items-center p-6 border-b'>
          <div className='flex items-center gap-2'>
            <Key size={20} className='text-[#555555]' />
            <h2 className='text-xl font-semibold'>
              {provider.charAt(0).toUpperCase() + provider.slice(1)} API Key
            </h2>
          </div>
          <button
            onClick={onClose}
            className='text-[#555555] cursor-pointer hover:text-gray-700 p-2 hover:scale-110 transition-transform keyboard-navigation'
            aria-label='Close API key modal'
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className='p-6'>
          <p className='text-[#555555] text-sm mb-4'>
            Enter your {provider.charAt(0).toUpperCase() + provider.slice(1)}{' '}
            API key to continue using this provider.
          </p>

          <div className='relative flex w-full items-center justify-center'>
            {!loading ? (
              <div className='relative flex p-2 items-center w-full'>
                <input
                  type={show ? 'text' : 'password'}
                  id='apiKey'
                  name='apiKey'
                  placeholder={
                    provider.charAt(0).toUpperCase() +
                    provider.slice(1) +
                    ' API Key'
                  }
                  required={true}
                  autoComplete='off'
                  className={`w-full pr-10 px-4 py-2 border text-[#555555]  ${
                    hasFieldError('apiKey')
                      ? 'border-red-500'
                      : 'border-[#999999]'
                  } rounded-lg shadow-sm keyboard-navigation `}
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
                  autoFocus
                />
                <button
                  type='button'
                  onClick={() => setShow((prev) => !prev)}
                  className='cursor-pointer absolute right-5 text-gray-500 hover:text-blue-600'
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
                className='absolute -bottom-6 left-2 text-red-500 text-sm'
                role='alert'
              >
                {getFieldError('apiKey')}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className='flex justify-end gap-3 p-6 border-t'>
          <button
            onClick={onClose}
            className='px-4 py-2 text-[#555555] border border-[#999999] rounded hover:bg-gray-50 transition-colors keyboard-navigation'
          >
            Cancel
          </button>
          <button
            onClick={saveKeys}
            disabled={loading || !apiKey.trim()}
            className='px-4 py-2 bg-[#555555] text-white rounded hover:bg-[#777777] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors keyboard-navigation'
          >
            {loading ? 'Saving...' : 'Save'}
          </button>
        </div>
      </div>
    </div>
  );
});
