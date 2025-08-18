import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ToggleSwitch } from '../ToggleSwitch';

describe('ToggleSwitch Component', () => {
  it('should render with initial value false by default', () => {
    render(<ToggleSwitch />);
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('should render with provided initial value', () => {
    render(<ToggleSwitch initialValue={true} />);
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('should work as controlled component with value prop', () => {
    const onChange = vi.fn();
    const { rerender } = render(
      <ToggleSwitch value={false} onChange={onChange} />
    );
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'false');
    
    // Click the toggle
    fireEvent.click(toggle);
    
    // onChange should be called with true
    expect(onChange).toHaveBeenCalledWith(true);
    
    // Component should still show false until parent updates value
    expect(toggle).toHaveAttribute('aria-checked', 'false');
    
    // Simulate parent updating the value
    rerender(<ToggleSwitch value={true} onChange={onChange} />);
    
    // Now it should show true
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('should work as uncontrolled component with initialValue', () => {
    const onChange = vi.fn();
    render(<ToggleSwitch initialValue={false} onChange={onChange} />);
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('aria-checked', 'false');
    
    // Click the toggle
    fireEvent.click(toggle);
    
    // onChange should be called with true
    expect(onChange).toHaveBeenCalledWith(true);
    
    // Component should update its own state
    expect(toggle).toHaveAttribute('aria-checked', 'true');
  });

  it('should handle disabled state correctly', () => {
    const onChange = vi.fn();
    render(<ToggleSwitch disabled={true} onChange={onChange} />);
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toBeDisabled();
    
    // Click should not work
    fireEvent.click(toggle);
    expect(onChange).not.toHaveBeenCalled();
    expect(toggle).toHaveAttribute('aria-checked', 'false');
  });

  it('should apply correct size classes', () => {
    const { rerender } = render(<ToggleSwitch size="x-small" />);
    
    let toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('w-8', 'h-4');
    
    rerender(<ToggleSwitch size="small" />);
    toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('w-12', 'h-6');
    
    rerender(<ToggleSwitch size="medium" />);
    toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('w-14', 'h-7');
    
    rerender(<ToggleSwitch size="large" />);
    toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('w-16', 'h-8');
  });

  it('should handle id and aria-label props', () => {
    render(
      <ToggleSwitch 
        id="test-toggle" 
        aria-label="Test toggle switch" 
      />
    );
    
    const toggle = screen.getByRole('switch');
    expect(toggle).toHaveAttribute('id', 'test-toggle');
    expect(toggle).toHaveAttribute('aria-label', 'Test toggle switch');
  });

  it('should show correct visual state for on/off', () => {
    const { rerender } = render(<ToggleSwitch value={false} />);
    
    let toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('bg-gray-300');
    
    rerender(<ToggleSwitch value={true} />);
    toggle = screen.getByRole('switch');
    expect(toggle).toHaveClass('bg-blue-500');
  });

  it('should handle rapid state changes correctly', () => {
    const onChange = vi.fn();
    render(<ToggleSwitch initialValue={false} onChange={onChange} />);
    
    const toggle = screen.getByRole('switch');
    
    // Rapid clicks
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    
    expect(onChange).toHaveBeenCalledTimes(3);
    expect(onChange.mock.calls).toEqual([[true], [false], [true]]);
  });
});