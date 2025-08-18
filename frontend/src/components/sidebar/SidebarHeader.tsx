import { Menu } from 'lucide-react';
import type { SidebarHeaderProps } from '@/types/sidebar';
import { SIDEBAR_STYLES, ACCESSIBILITY } from '@/constants/sidebar';

export function SidebarHeader({ isOpen, onToggle }: SidebarHeaderProps) {
  return (
    <button
      onClick={onToggle}
      className={SIDEBAR_STYLES.TOGGLE_BUTTON}
      aria-label={ACCESSIBILITY.LABELS.TOGGLE_SIDEBAR}
      aria-expanded={isOpen}
      aria-controls='sidebar-panel'
      type='button'
    >
      <Menu size='full' aria-hidden='true' />
    </button>
  );
}
