import { memo, useMemo } from 'react';
import { SidebarHeader, SidebarNavigation, SidebarPanel } from '@/components/sidebar';
import { useSidebarData } from '@/hooks/useSidebarData';
import { useSidebarState } from '@/hooks/useSidebarState';
import type { SidebarProps, NavigationItems } from '@/types/sidebar';
import { SIDEBAR_STYLES } from '@/constants/sidebar';
import OpenAILogo from '@/assets/OpenAILogo.svg?react';
import OllamaLogo from '@/assets/OllamaLogo.svg?react';

export const Sidebar = memo(function Sidebar({ className }: SidebarProps) {
  const { navigationItems, isLoading, error } = useSidebarData();
  const {
    isOpen,
    selectedProviderIndex,
    selectedModelIndex,
    toggleSidebar,
    selectProvider,
    selectModel,
  } = useSidebarState();

  // Add icons to navigation items
  const navigationItemsWithIcons: NavigationItems = useMemo(() => {
    return navigationItems.map(item => ({
      ...item,
      icon: item.name === 'Ollama' 
        ? <OllamaLogo className='w-6 h-6 fill-white' />
        : item.name === 'OpenAI'
        ? <OpenAILogo className='w-6 h-6 fill-white' />
        : item.icon
    }));
  }, [navigationItems]);

  const selectedItem = navigationItemsWithIcons[selectedProviderIndex] || null;

  const containerClasses = className 
    ? `${SIDEBAR_STYLES.BASE} ${className}`
    : SIDEBAR_STYLES.BASE;

  return (
    <div className={containerClasses}>
      <SidebarHeader 
        isOpen={isOpen} 
        onToggle={toggleSidebar} 
      />
      
      <div className="flex h-full">
        <SidebarNavigation
          items={navigationItemsWithIcons}
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
