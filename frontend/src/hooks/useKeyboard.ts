import { useEffect, useCallback, useRef, useState } from 'react';

export interface KeyboardShortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  meta?: boolean;
  preventDefault?: boolean;
  callback: (event: KeyboardEvent) => void;
}

export function useKeyboard(shortcuts: KeyboardShortcut[]): void {
  const shortcutsRef = useRef(shortcuts);
  shortcutsRef.current = shortcuts;

  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    const activeShortcuts = shortcutsRef.current;

    for (const shortcut of activeShortcuts) {
      const {
        key,
        ctrl = false,
        shift = false,
        alt = false,
        meta = false,
        preventDefault = true,
        callback,
      } = shortcut;

      const isMatch =
        event.key.toLowerCase() === key.toLowerCase() &&
        event.ctrlKey === ctrl &&
        event.shiftKey === shift &&
        event.altKey === alt &&
        event.metaKey === meta;

      if (isMatch) {
        if (preventDefault) {
          event.preventDefault();
        }
        callback(event);
        break; // Only trigger the first matching shortcut
      }
    }
  }, []);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

export function useKeyPress(targetKey: string): boolean {
  const [keyPressed, setKeyPressed] = useState(false);

  const downHandler = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === targetKey) {
        setKeyPressed(true);
      }
    },
    [targetKey]
  );

  const upHandler = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === targetKey) {
        setKeyPressed(false);
      }
    },
    [targetKey]
  );

  useEffect(() => {
    document.addEventListener('keydown', downHandler);
    document.addEventListener('keyup', upHandler);

    return () => {
      document.removeEventListener('keydown', downHandler);
      document.removeEventListener('keyup', upHandler);
    };
  }, [downHandler, upHandler]);

  return keyPressed;
}

export function useEscapeKey(callback: () => void): void {
  const callbackRef = useRef(callback);
  callbackRef.current = callback;

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        callbackRef.current();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, []);
}

// Common keyboard shortcuts
export const KEYBOARD_SHORTCUTS = {
  SEND_MESSAGE: { key: 'Enter', ctrl: true },
  NEW_CHAT: { key: 'n', ctrl: true },
  CLEAR_CHAT: { key: 'k', ctrl: true },
  TOGGLE_SIDEBAR: { key: 'b', ctrl: true },
  SEARCH: { key: 'f', ctrl: true },
  SETTINGS: { key: ',', ctrl: true },
  HELP: { key: '/', shift: true },
} as const;