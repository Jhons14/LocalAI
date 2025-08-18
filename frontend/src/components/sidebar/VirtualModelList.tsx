import { memo, useMemo } from 'react';
import { ModelItem } from './ModelItem';
import type { ModelListProps } from '@/types/sidebar';
import { SIDEBAR_STYLES, PERFORMANCE } from '@/constants/sidebar';

export const VirtualModelList = memo(function VirtualModelList({
  models,
  selectedIndex,
  onModelSelect,
  maxItemsBeforeVirtualization = PERFORMANCE.VIRTUAL_SCROLL_THRESHOLD,
}: ModelListProps) {
  const shouldUseVirtualScrolling = models.length > maxItemsBeforeVirtualization;

  const renderedModels = useMemo(() => {
    return models.map((model, index) => (
      <ModelItem
        key={`${model.provider}-${model.model}`}
        model={model}
        index={index}
        isSelected={selectedIndex === index}
        onClick={onModelSelect}
      />
    ));
  }, [models, selectedIndex, onModelSelect]);

  if (shouldUseVirtualScrolling) {
    return (
      <div className={SIDEBAR_STYLES.SCROLL_CONTAINER}>
        <div className={SIDEBAR_STYLES.MODEL_COUNT}>
          {models.length} models available
        </div>
        <div role="listbox" aria-label="Available models">
          {renderedModels}
        </div>
      </div>
    );
  }

  return (
    <ul role="listbox" aria-label="Available models">
      {renderedModels.map((item, index) => (
        <li key={models[index].model} role="none">
          {item}
        </li>
      ))}
    </ul>
  );
});