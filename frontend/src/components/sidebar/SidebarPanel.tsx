import { memo, useEffect, useState } from 'react';
import { ModelList } from './ModelList';
import type { SidebarPanelProps } from '@/types/sidebar';
import { SIDEBAR_STYLES } from '@/constants/sidebar';

export const SidebarPanel = memo(function SidebarPanel({
  isOpen,
  selectedItem,
  selectedModelIndex,
  onModelSelect,
}: SidebarPanelProps) {
  const [render, setRender] = useState(false);

  // Mount when opening; keep mounted while closing so fade-out can play
  useEffect(() => {
    if (isOpen) setRender(true);
  }, [isOpen]);

  const handleTransitionEnd = () => {
    if (!isOpen) setRender(false); // unmount *after* fade/slide finishes
  };

  const panelClasses = [
    SIDEBAR_STYLES.PANEL_BASE,
    isOpen ? SIDEBAR_STYLES.PANEL_OPEN : SIDEBAR_STYLES.PANEL_CLOSED,
  ].join(' ');

  const titleClasses = [
    'block transition-opacity duration-200',
    isOpen ? 'opacity-100' : 'opacity-0',
  ].join(' ');

  const contentClasses = [
    'overflow-hidden transition-opacity duration-200',
    isOpen ? 'opacity-100' : 'opacity-0',
  ].join(' ');

  return (
    <nav
      id="sidebar-panel"
      onTransitionEnd={handleTransitionEnd}
      className={panelClasses}
      aria-hidden={!isOpen}
    >
      <h2 className="overflow-hidden border-b h-11 border-b-[#999999] text-center py-2 font-bold text-xl">
        <span className={titleClasses}>
          {selectedItem?.name || ''}
        </span>
      </h2>

      <div className={contentClasses}>
        {render && selectedItem && (
          <ModelList
            models={selectedItem.subItems || []}
            selectedIndex={selectedModelIndex}
            onModelSelect={onModelSelect}
            isLoading={selectedItem.isLoading}
            error={selectedItem.error}
          />
        )}
      </div>
    </nav>
  );
});