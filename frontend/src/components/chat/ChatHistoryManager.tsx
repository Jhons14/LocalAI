import { memo, useState, useCallback } from 'react';
import { Trash2, Download, Clock, MessageSquare } from 'lucide-react';
import { usePersistence } from '@/hooks/usePersistentState';
import { useMobileFirst } from '@/hooks/useResponsive';
import { useToast } from '@/hooks/useToast';
import { useEscapeKey } from '@/hooks/useKeyboard';
import { LoadingButton } from '@/components/ui/LoadingStates';
import { formatRelativeTime } from '@/utils/common';
import { X } from 'lucide-react';

interface ChatHistoryManagerProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ChatHistoryManager = memo(function ChatHistoryManager({
  isOpen,
  onClose,
}: ChatHistoryManagerProps) {
  const { isMobile } = useMobileFirst();
  const { success, error: showError } = useToast();
  const {
    getAllThreads,
    deleteChatThread,
    clearAllHistory,
    exportData,
    getStorageUsage,
  } = usePersistence();

  const [loading, setLoading] = useState(false);
  const [threads, setThreads] = useState(() => getAllThreads());

  // Close on Escape key
  useEscapeKey(() => {
    if (isOpen) onClose();
  });

  const refreshThreads = useCallback(() => {
    setThreads(getAllThreads());
  }, [getAllThreads]);

  const handleDeleteThread = useCallback(
    async (threadId: string) => {
      if (!confirm('Are you sure you want to delete this conversation?')) {
        return;
      }

      setLoading(true);
      try {
        const success_result = deleteChatThread(threadId);
        if (success_result) {
          refreshThreads();
        }
      } catch (error) {
        showError('Delete Failed', 'Failed to delete conversation');
      } finally {
        setLoading(false);
      }
    },
    [deleteChatThread, refreshThreads, showError]
  );

  const handleClearAll = useCallback(async () => {
    if (
      !confirm(
        'Are you sure you want to delete ALL conversations? This cannot be undone.'
      )
    ) {
      return;
    }

    setLoading(true);
    try {
      const success_result = clearAllHistory();
      if (success_result) {
        refreshThreads();
      }
    } catch (error) {
      showError('Clear Failed', 'Failed to clear chat history');
    } finally {
      setLoading(false);
    }
  }, [clearAllHistory, refreshThreads, showError]);

  const handleExport = useCallback(() => {
    try {
      exportData();
      success('Export Complete', 'Chat history has been exported successfully');
    } catch (error) {
      showError('Export Failed', 'Failed to export chat history');
    }
  }, [exportData, success, showError]);

  const formatDate = useCallback((timestamp: number) => {
    return formatRelativeTime(timestamp);
  }, []);

  const storageUsage = getStorageUsage();

  if (!isOpen) return null;

  return (
    <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 '>
      <div
        className={`bg-white rounded-lg shadow-xl ${
          isMobile ? 'w-full h-full' : 'w-full max-w-2xl max-h-[80vh]'
        } flex flex-col`}
      >
        {/* Header */}
        <div className='flex justify-between items-center p-6 border-b'>
          <h2 className='text-xl font-semibold'>Chat History</h2>
          <button
            onClick={onClose}
            className='text-[#555555] cursor-pointer hover:text-gray-700 p-2 hover:scale-110 transition-transform keyboard-navigation'
            aria-label='Close chat history'
          >
            <X size={20} />
          </button>
        </div>

        {/* Storage Usage */}
        <div className='px-6 py-4 bg-gray-50 border-b'>
          <div className='flex items-center justify-between text-sm text-gray-600'>
            <span>Storage Usage: {storageUsage.percentage.toFixed(1)}%</span>
            <span>{(storageUsage.used / 1024).toFixed(1)}KB used</span>
          </div>
          <div className='w-full bg-gray-200 rounded-full h-2 mt-2'>
            <div
              className={`h-2 rounded-full ${
                storageUsage.percentage > 80
                  ? 'bg-red-500'
                  : storageUsage.percentage > 60
                  ? 'bg-yellow-500'
                  : 'bg-green-500'
              }`}
              style={{ width: `${Math.min(storageUsage.percentage, 100)}%` }}
            />
          </div>
        </div>

        {/* Actions */}
        <div className='flex gap-2 p-6 border-b'>
          <LoadingButton
            isLoading={loading}
            onClick={handleExport}
            className='flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600'
          >
            <Download size={16} />
            Export
          </LoadingButton>

          <LoadingButton
            isLoading={loading}
            onClick={handleClearAll}
            className='flex items-center gap-2 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600'
          >
            <Trash2 size={16} />
            Clear All
          </LoadingButton>

          <LoadingButton
            isLoading={loading}
            onClick={refreshThreads}
            className='flex items-center gap-2 px-4 py-2 bg-[#555555] text-white rounded hover:bg-gray-600'
          >
            Refresh
          </LoadingButton>
        </div>

        {/* Thread List */}
        <div className='flex-1 overflow-y-auto p-6'>
          {threads.length === 0 ? (
            <div className='text-center text-[#555555] py-8'>
              <MessageSquare size={48} className='mx-auto mb-4 opacity-50' />
              <p>No chat history found</p>
              <p className='text-sm mt-2'>
                Start a conversation to see it here
              </p>
            </div>
          ) : (
            <div className='space-y-3'>
              {threads.map((thread) => (
                <div
                  key={thread.id}
                  className='flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50'
                >
                  <div className='flex-1 min-w-0'>
                    <div className='flex items-center gap-2 mb-1'>
                      <span className='font-medium text-sm text-gray-900'>
                        {thread.model}
                      </span>
                      <span className='text-xs text-[#555555] bg-gray-100 px-2 py-1 rounded'>
                        {thread.provider}
                      </span>
                    </div>
                    <div className='flex items-center gap-2 text-sm text-gray-600'>
                      <Clock size={14} />
                      <span>{formatDate(thread.lastUpdated)}</span>
                      <span className='ml-2'>•</span>
                      <span>{thread.messageCount} messages</span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDeleteThread(thread.id)}
                    disabled={loading}
                    className='text-red-500 hover:text-red-700 p-2 keyboard-navigation cursor-pointer'
                    aria-label={`Delete conversation with ${thread.model}`}
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
