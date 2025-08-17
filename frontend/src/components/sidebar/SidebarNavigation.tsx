import { memo } from 'react';
import { SidebarNavigationItem } from './SidebarNavigationItem';
import type { SidebarNavigationProps } from '@/types/sidebar';
import { SIDEBAR_STYLES, ACCESSIBILITY } from '@/constants/sidebar';

export const SidebarNavigation = memo(function SidebarNavigation({
  items,
  selectedIndex,
  isOpen,
  onItemSelect,
  onToggle,
}: SidebarNavigationProps) {
  return (
    <nav
      className={SIDEBAR_STYLES.NAV_CONTAINER}
      role='navigation'
      aria-label={ACCESSIBILITY.LABELS.PROVIDER_LIST}
    >
      {items.map((item, index) => (
        <SidebarNavigationItem
          key={item.name}
          item={item}
          index={index}
          isOpen={isOpen}
          isSelected={selectedIndex === index}
          onSelect={onItemSelect}
          onToggle={onToggle}
        />
      ))}
    </nav>
  );
});
