import { memo } from 'react';

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
}

export const Skeleton = memo(function Skeleton({
  className = '',
  width = '100%',
  height = '1rem',
}: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-gray-200 rounded ${className}`}
      style={{ width, height }}
    />
  );
});

export const MessageSkeleton = memo(function MessageSkeleton({
  isUser = false,
}: {
  isUser?: boolean;
}) {
  return (
    <div
      className={`mb-4 ${isUser ? 'flex justify-end' : 'flex justify-start'}`}
    >
      <div
        className={`max-w-md ${
          isUser ? 'bg-gray-100' : 'bg-white'
        } p-4 rounded-lg`}
      >
        <div className='space-y-2'>
          <Skeleton height='0.875rem' width='80%' />
          <Skeleton height='0.875rem' width='60%' />
          <Skeleton height='0.875rem' width='90%' />
        </div>
      </div>
    </div>
  );
});

export const ChatSkeleton = memo(function ChatSkeleton() {
  return (
    <div className='flex-1 overflow-y-auto p-4'>
      <div className='max-w-4xl mx-auto space-y-4'>
        <MessageSkeleton />
        <MessageSkeleton isUser />
        <MessageSkeleton />
        <MessageSkeleton isUser />
        <MessageSkeleton />
      </div>
    </div>
  );
});

export const ModelListSkeleton = memo(function ModelListSkeleton() {
  return (
    <div className='space-y-2 p-2'>
      {Array.from({ length: 5 }).map((_, index) => (
        <div key={index} className='flex items-center space-x-2 p-2'>
          <Skeleton width='1rem' height='1rem' className='rounded-full' />
          <Skeleton height='0.875rem' width={`${60 + Math.random() * 40}%`} />
        </div>
      ))}
    </div>
  );
});

export const SidebarSkeleton = memo(function SidebarSkeleton() {
  return (
    <div className='w-64 text-white p-4'>
      <div className='space-y-4'>
        <Skeleton height='2rem' width='70%' className='bg-gray-700' />
        <div className='space-y-2'>
          {Array.from({ length: 3 }).map((_, index) => (
            <div key={index} className='flex items-center space-x-2'>
              <Skeleton
                width='1.5rem'
                height='1.5rem'
                className='bg-gray-700 rounded'
              />
              <Skeleton height='1rem' width='60%' className='bg-gray-700' />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
});

export const TopBarSkeleton = memo(function TopBarSkeleton() {
  return (
    <div className='flex justify-between items-center p-4 border-b border-gray-200'>
      <Skeleton height='1.5rem' width='200px' />
      <div className='flex items-center space-x-4'>
        <Skeleton height='2rem' width='120px' />
        <Skeleton height='2rem' width='80px' />
      </div>
    </div>
  );
});

export const LoadingSpinner = memo(function LoadingSpinner({
  size = 'md',
  className = '',
}: {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={`${sizeClasses[size]} ${className}`}>
      <div className='animate-spin rounded-full border-2 border-gray-300 border-t-blue-600' />
    </div>
  );
});
