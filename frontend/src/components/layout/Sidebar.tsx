import { memo } from 'react';
import {
  SidebarHeader,
  SidebarNavigation,
  SidebarPanel,
} from '@/components/sidebar';
import { useSidebarData } from '@/hooks/useSidebarData';
import { useSidebarState } from '@/hooks/useSidebarState';
import type { SidebarProps } from '@/types/sidebar';
import { SIDEBAR_STYLES } from '@/constants/sidebar';

export const Sidebar = memo(function Sidebar({ className }: SidebarProps) {
  const { navigationItems } = useSidebarData();
  const {
    isOpen,
    selectedProviderIndex,
    selectedModelIndex,
    toggleSidebar,
    selectProvider,
    selectModel,
  } = useSidebarState();

  const selectedItem = navigationItems[selectedProviderIndex] || null;

  const containerClasses = className
    ? `${SIDEBAR_STYLES.BASE} ${className}`
    : SIDEBAR_STYLES.BASE;

  return (
    <div className={containerClasses}>
      <SidebarHeader isOpen={isOpen} onToggle={toggleSidebar} />

      <div className='flex h-full'>
        <SidebarNavigation
          items={navigationItems}
          selectedIndex={selectedProviderIndex}
          isOpen={isOpen}
          onItemSelect={selectProvider}
          onToggle={toggleSidebar}
        />

        <SidebarPanel
          isOpen={isOpen}
          selectedItem={selectedItem}
          selectedModelIndex={selectedModelIndex}
          onModelSelect={selectModel}
        />
      </div>
    </div>
  );
});
