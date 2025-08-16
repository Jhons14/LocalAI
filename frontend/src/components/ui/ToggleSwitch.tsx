import React, { useState } from 'react';

type ToggleSwitchSize = 'x-small' | 'small' | 'medium' | 'large';

interface ToggleSwitchProps {
  initialValue?: boolean;
  onChange?: (value: boolean) => void;
  disabled?: boolean;
  size?: ToggleSwitchSize;
}

export const ToggleSwitch: React.FC<ToggleSwitchProps> = ({
  initialValue = false,
  onChange,
  disabled = false,
  size = 'medium', // 'small', 'medium', 'large'
}) => {
  const [isOn, setIsOn] = useState(initialValue);

  const handleToggle = () => {
    if (disabled) return;

    const newValue = !isOn;
    setIsOn(newValue);

    if (onChange) {
      onChange(newValue);
    }
  };

  // Size variants
  const sizeClasses = {
    'x-small': 'w-8 h-4',
    small: 'w-12 h-6',
    medium: 'w-14 h-7',
    large: 'w-16 h-8',
  };

  const circleClasses = {
    'x-small': 'w-3 h-3',
    small: 'w-4 h-4',
    medium: 'w-5 h-5',
    large: 'w-6 h-6',
  };
  return (
    <button
      type='button'
      onClick={handleToggle}
      disabled={disabled}
      className={`
        ${sizeClasses[size]}
        relative inline-flex items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
        ${isOn ? 'bg-blue-500' : 'bg-gray-300'}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
      role='switch'
      aria-checked={isOn}
    >
      <span
        className={`
          ${circleClasses[size]}
          inline-block rounded-full bg-white shadow transform transition-transform duration-200 ease-in-out
          ${isOn ? 'translate-x-5' : 'translate-x-1'}
          ${size === 'x-small' && (isOn ? 'translate-x-4' : 'translate-x-1')}
          
          ${size === 'small' && (isOn ? 'translate-x-4' : 'translate-x-1')}
          ${size === 'large' && (isOn ? 'translate-x-6' : 'translate-x-1')}
        `}
      />
    </button>
  );
};
