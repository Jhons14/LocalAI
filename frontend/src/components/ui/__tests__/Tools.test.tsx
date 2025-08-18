import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Tools } from '../Tools';
import type { ActiveModel } from '@/types/chat';

// Mock the chat history context
const mockSetActiveModel = vi.fn();
vi.mock('@/hooks/useChatHistoryContext', () => ({
  useChatHistoryContext: () => ({
    setActiveModel: mockSetActiveModel,
  }),
}));

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
  Hammer: () => <div data-testid="hammer-icon">Hammer</div>,
}));

describe('Tools Component', () => {
  const mockActiveModel: ActiveModel = {
    model: 'gpt-4',
    provider: 'openai',
    thread_id: 'test-thread',
    toolkits: [],
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render null when no model is provided', () => {
    const { container } = render(<Tools model={undefined} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render tools button when model is provided', () => {
    render(<Tools model={mockActiveModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    expect(toolsButton).toBeInTheDocument();
    expect(screen.getByTestId('hammer-icon')).toBeInTheDocument();
  });

  it('should show tools dropdown when button is clicked', async () => {
    render(<Tools model={mockActiveModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    // Wait for dropdown to appear
    await waitFor(() => {
      expect(screen.getByText('Gmail')).toBeInTheDocument();
      expect(screen.getByText('Asana')).toBeInTheDocument();
    });
  });

  it('should reflect active model toolkits in toggle states', async () => {
    const modelWithTools: ActiveModel = {
      ...mockActiveModel,
      toolkits: ['Gmail'],
    };

    render(<Tools model={modelWithTools} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    await waitFor(() => {
      const gmailToggle = screen.getByLabelText('Toggle Gmail tool');
      const asanaToggle = screen.getByLabelText('Toggle Asana tool');
      
      // Gmail should be checked (enabled)
      expect(gmailToggle).toHaveAttribute('aria-checked', 'true');
      // Asana should not be checked (disabled)
      expect(asanaToggle).toHaveAttribute('aria-checked', 'false');
    });
  });

  it('should update active model when tool is toggled', async () => {
    render(<Tools model={mockActiveModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    await waitFor(() => {
      const gmailToggle = screen.getByLabelText('Toggle Gmail tool');
      fireEvent.click(gmailToggle);
    });

    expect(mockSetActiveModel).toHaveBeenCalledWith({
      ...mockActiveModel,
      toolkits: ['Gmail'],
    });
  });

  it('should remove tool from active model when toggled off', async () => {
    const modelWithTools: ActiveModel = {
      ...mockActiveModel,
      toolkits: ['Gmail', 'Asana'],
    };

    render(<Tools model={modelWithTools} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    await waitFor(() => {
      const gmailToggle = screen.getByLabelText('Toggle Gmail tool');
      fireEvent.click(gmailToggle);
    });

    expect(mockSetActiveModel).toHaveBeenCalledWith({
      ...modelWithTools,
      toolkits: ['Asana'], // Gmail should be removed
    });
  });

  it('should handle multiple tool toggles correctly', async () => {
    render(<Tools model={mockActiveModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    await waitFor(async () => {
      const gmailToggle = screen.getByLabelText('Toggle Gmail tool');
      const asanaToggle = screen.getByLabelText('Toggle Asana tool');
      
      // Enable Gmail
      fireEvent.click(gmailToggle);
      
      // Enable Asana
      fireEvent.click(asanaToggle);
    });

    // Should be called for both toggles
    expect(mockSetActiveModel).toHaveBeenCalledTimes(2);
    
    // Last call should have both tools
    const lastCall = mockSetActiveModel.mock.calls[mockSetActiveModel.mock.calls.length - 1];
    expect(lastCall[0].toolkits).toContain('Asana');
  });

  it('should sync state when active model changes', () => {
    const { rerender } = render(<Tools model={mockActiveModel} />);
    
    // Change model to have different toolkits
    const updatedModel: ActiveModel = {
      ...mockActiveModel,
      toolkits: ['Gmail'],
    };
    
    rerender(<Tools model={updatedModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    // Should reflect the new toolkits state
    waitFor(() => {
      const gmailToggle = screen.getByLabelText('Toggle Gmail tool');
      expect(gmailToggle).toHaveAttribute('aria-checked', 'true');
    });
  });

  it('should close dropdown when clicking outside', async () => {
    render(
      <div>
        <Tools model={mockActiveModel} />
        <div data-testid="outside-element">Outside</div>
      </div>
    );
    
    const toolsButton = screen.getByLabelText('Tools');
    fireEvent.click(toolsButton);

    // Dropdown should be open
    await waitFor(() => {
      expect(screen.getByText('Gmail')).toBeInTheDocument();
    });

    // Click outside
    const outsideElement = screen.getByTestId('outside-element');
    fireEvent.click(outsideElement);

    // Dropdown should close
    await waitFor(() => {
      expect(screen.queryByText('Gmail')).not.toBeInTheDocument();
    });
  });

  it('should have proper accessibility attributes', async () => {
    render(<Tools model={mockActiveModel} />);
    
    const toolsButton = screen.getByLabelText('Tools');
    
    // Button should have proper attributes
    expect(toolsButton).toHaveAttribute('aria-expanded', 'false');
    expect(toolsButton).toHaveAttribute('type', 'button');
    
    fireEvent.click(toolsButton);
    
    await waitFor(() => {
      expect(toolsButton).toHaveAttribute('aria-expanded', 'true');
      
      // Tools should have proper labels
      expect(screen.getByLabelText('Toggle Gmail tool')).toBeInTheDocument();
      expect(screen.getByLabelText('Toggle Asana tool')).toBeInTheDocument();
    });
  });
});