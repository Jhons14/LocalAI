import { memo } from 'react';
import type { SidebarItemProps } from '@/types/sidebar';
import { SIDEBAR_STYLES, ACCESSIBILITY } from '@/constants/sidebar';

export const SidebarNavigationItem = memo(function SidebarNavigationItem({
  item,
  index,
  isOpen,
  isSelected,
  onSelect,
  onToggle,
}: SidebarItemProps) {
  const handleClick = () => {
    if (isSelected) {
      onToggle();
      return;
    }
    onSelect(index);
  };

  const buttonClasses = `${SIDEBAR_STYLES.ITEM_BUTTON} ${
    isSelected ? SIDEBAR_STYLES.ITEM_SELECTED : ''
  }`;

  return (
    <button
      className={buttonClasses}
      type='button'
      onClick={handleClick}
      aria-label={`${ACCESSIBILITY.LABELS.SELECT_PROVIDER} ${item.name}`}
      aria-pressed={isSelected}
      aria-expanded={isSelected && isOpen}
      aria-controls={isSelected ? 'sidebar-panel' : undefined}
      title={item.name}
    >
      <div aria-hidden='true'>{item.icon}</div>
      <span className='sr-only'>{item.name}</span>
    </button>
  );
});
