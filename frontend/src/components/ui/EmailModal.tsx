import { useState, memo, useCallback, useEffect } from 'react';
import { Mail, X } from 'lucide-react';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useChatHistoryContext } from '@/hooks/useChatHistoryContext';
import { useEscapeKey } from '@/hooks/useKeyboard';

interface EmailModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const EmailModal = memo(function EmailModal({
  isOpen,
  onClose,
}: EmailModalProps) {
  const { userEmail, setUserEmail } = useChatHistoryContext();
  const [tempEmail, setTempEmail] = useState(userEmail);
  const { isMobile } = useMobileFirst();

  // Update tempEmail when userEmail changes
  useEffect(() => {
    setTempEmail(userEmail);
  }, [userEmail]);

  // Close on Escape key
  useEscapeKey(() => {
    if (isOpen) onClose();
  });

  const handleSave = useCallback(() => {
    if (tempEmail.trim()) {
      setUserEmail(tempEmail.trim());
      onClose();
    }
  }, [tempEmail, setUserEmail, onClose]);

  const handleCancel = useCallback(() => {
    setTempEmail(userEmail);
    onClose();
  }, [userEmail, onClose]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter') {
        handleSave();
      }
    },
    [handleSave]
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
            <Mail size={20} className='text-[#555555]' />
            <h2 className='text-xl font-semibold'>Set Email</h2>
          </div>
          <button
            onClick={onClose}
            className='text-[#555555] cursor-pointer hover:text-gray-700 p-2 hover:scale-110 transition-transform keyboard-navigation'
            aria-label='Close email modal'
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className='p-6'>
          <p className='text-[#555555] text-sm mb-4'>
            Enter your email address for identification and tool integration.
          </p>

          <div className='relative flex w-full items-center justify-center'>
            <div className='relative flex p-2 items-center w-full'>
              <input
                type='email'
                id='email'
                name='email'
                placeholder='Enter your email'
                required={true}
                autoComplete='email'
                className='w-full px-4 py-2 border text-[#555555] border-[#999999] rounded-lg shadow-sm keyboard-navigation focus:outline-none focus:ring-2 focus:ring-[#555555] focus:border-transparent'
                value={tempEmail}
                onChange={(e) => setTempEmail(e.target.value)}
                onKeyDown={handleKeyPress}
                autoFocus
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className='flex justify-end gap-3 p-6 border-t'>
          <button
            onClick={handleCancel}
            className='px-4 py-2 text-[#555555] border border-[#999999] rounded hover:bg-gray-50 transition-colors keyboard-navigation'
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!tempEmail.trim()}
            className='px-4 py-2 bg-[#555555] text-white rounded hover:bg-[#777777] disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors keyboard-navigation'
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
});