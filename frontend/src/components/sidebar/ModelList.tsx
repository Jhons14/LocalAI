import { memo } from 'react';
import { VirtualModelList } from './VirtualModelList';
import { ModelListSkeleton } from '@/components/ui/SkeletonLoader';
import type { ModelListProps } from '@/types/sidebar';
import { SIDEBAR_STYLES } from '@/constants/sidebar';

export const ModelList = memo(function ModelList({
  models,
  selectedIndex,
  onModelSelect,
  isLoading = false,
  error = null,
  maxItemsBeforeVirtualization,
}: ModelListProps) {
  if (error) {
    return (
      <div className={SIDEBAR_STYLES.ERROR_TEXT} role="alert">
        {error}
      </div>
    );
  }

  if (isLoading) {
    return <ModelListSkeleton />;
  }

  if (models.length === 0) {
    return (
      <div className="text-sm text-gray-400 text-center p-2">
        No models available
      </div>
    );
  }

  return (
    <VirtualModelList
      models={models}
      selectedIndex={selectedIndex}
      onModelSelect={onModelSelect}
      maxItemsBeforeVirtualization={maxItemsBeforeVirtualization}
    />
  );
});