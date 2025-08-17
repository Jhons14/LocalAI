import { memo } from 'react';
import type { ModelItemProps } from '@/types/sidebar';
import { SIDEBAR_STYLES } from '@/constants/sidebar';

export const ModelItem = memo(function ModelItem({ 
  model, 
  index, 
  isSelected, 
  onClick 
}: ModelItemProps) {
  const handleClick = () => {
    onClick(index, model);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      className={`${SIDEBAR_STYLES.MODEL_BUTTON} ${
        isSelected ? SIDEBAR_STYLES.MODEL_SELECTED : ''
      }`}
      type="button"
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      aria-selected={isSelected}
      role="option"
      tabIndex={isSelected ? 0 : -1}
      title={`${model.title} (${model.provider})`}
    >
      <span className="truncate text-sm">
        {model.title}
      </span>
    </button>
  );
});