import { memo, useMemo, useRef, useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { ChatMessage } from '@/types/chat';

interface VirtualizedMessageListProps {
  messages: ChatMessage[];
  renderMessage: (message: ChatMessage, index: number) => React.ReactNode;
  containerHeight: number;
  itemHeight: number;
  overscan?: number;
}

export const VirtualizedMessageList = memo(function VirtualizedMessageList({
  messages,
  renderMessage,
  containerHeight,
  itemHeight,
  overscan = 5,
}: VirtualizedMessageListProps) {
  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  }, []);

  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      messages.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, overscan, messages.length]);

  const visibleMessages = useMemo(() => {
    return messages.slice(visibleRange.startIndex, visibleRange.endIndex + 1);
  }, [messages, visibleRange]);

  const totalHeight = messages.length * itemHeight;
  const offsetY = visibleRange.startIndex * itemHeight;

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (containerRef.current) {
      const isNearBottom = 
        scrollTop + containerHeight >= totalHeight - itemHeight * 2;
      
      if (isNearBottom) {
        containerRef.current.scrollTop = totalHeight - containerHeight;
      }
    }
  }, [messages.length, totalHeight, containerHeight, itemHeight, scrollTop]);

  return (
    <div
      ref={containerRef}
      className="flex-1 overflow-y-auto"
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: totalHeight, position: 'relative' }}>
        <div
          style={{
            position: 'absolute',
            top: offsetY,
            left: 0,
            right: 0,
          }}
        >
          <AnimatePresence>
            {visibleMessages.map((message, index) => {
              const actualIndex = visibleRange.startIndex + index;
              return (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  style={{ height: itemHeight }}
                >
                  {renderMessage(message, actualIndex)}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
});

// Hook for dynamic height calculation
export function useMessageHeight() {
  const [heights, setHeights] = useState<Map<string, number>>(new Map());

  const measureHeight = useCallback((messageId: string, height: number) => {
    setHeights(prev => {
      const newHeights = new Map(prev);
      newHeights.set(messageId, height);
      return newHeights;
    });
  }, []);

  const getHeight = useCallback((messageId: string, defaultHeight: number = 100) => {
    return heights.get(messageId) || defaultHeight;
  }, [heights]);

  return { measureHeight, getHeight, heights };
}