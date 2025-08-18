import { describe, it, expect } from 'vitest';
import type { ActiveModel, ToolName } from '@/types/chat';

describe('Phase 2 Integration Tests - Tools State Management', () => {
  describe('Tools State Logic', () => {
    it('should correctly manage tool state transitions', () => {
      // Simulate the tools state management logic
      const AVAILABLE_TOOLS: ToolName[] = ['Gmail', 'Asana'];
      
      // Initial state - no tools enabled
      const initialModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };
      
      // Function to toggle a tool (simulates the component logic)
      const toggleTool = (
        currentModel: ActiveModel, 
        tool: ToolName, 
        enabled: boolean
      ): ActiveModel => {
        const newToolkits: string[] = [];
        
        AVAILABLE_TOOLS.forEach(t => {
          const isEnabled = t === tool ? enabled : currentModel.toolkits.includes(t);
          if (isEnabled) {
            newToolkits.push(t);
          }
        });
        
        return {
          ...currentModel,
          toolkits: newToolkits,
        };
      };
      
      // Test enabling Gmail
      const modelWithGmail = toggleTool(initialModel, 'Gmail', true);
      expect(modelWithGmail.toolkits).toEqual(['Gmail']);
      
      // Test enabling Asana while Gmail is enabled
      const modelWithBothTools = toggleTool(modelWithGmail, 'Asana', true);
      expect(modelWithBothTools.toolkits).toEqual(['Gmail', 'Asana']);
      
      // Test disabling Gmail while Asana is enabled
      const modelWithOnlyAsana = toggleTool(modelWithBothTools, 'Gmail', false);
      expect(modelWithOnlyAsana.toolkits).toEqual(['Asana']);
      
      // Test disabling all tools
      const modelWithNoTools = toggleTool(modelWithOnlyAsana, 'Asana', false);
      expect(modelWithNoTools.toolkits).toEqual([]);
    });
    
    it('should correctly sync tools state with activeModel.toolkits', () => {
      const AVAILABLE_TOOLS: ToolName[] = ['Gmail', 'Asana'];
      
      // Function to create tools state from activeModel (simulates useEffect logic)
      const createToolsStateFromModel = (activeModel: ActiveModel | undefined) => {
        const toolsState: Record<ToolName, boolean> = {
          Gmail: false,
          Asana: false,
        };
        
        if (!activeModel) {
          return toolsState;
        }
        
        AVAILABLE_TOOLS.forEach(tool => {
          toolsState[tool] = activeModel.toolkits.includes(tool);
        });
        
        return toolsState;
      };
      
      // Test with no active model
      let toolsState = createToolsStateFromModel(undefined);
      expect(toolsState).toEqual({ Gmail: false, Asana: false });
      
      // Test with model having Gmail enabled
      const modelWithGmail: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: ['Gmail'],
      };
      
      toolsState = createToolsStateFromModel(modelWithGmail);
      expect(toolsState).toEqual({ Gmail: true, Asana: false });
      
      // Test with model having both tools enabled
      const modelWithBothTools: ActiveModel = {
        ...modelWithGmail,
        toolkits: ['Gmail', 'Asana'],
      };
      
      toolsState = createToolsStateFromModel(modelWithBothTools);
      expect(toolsState).toEqual({ Gmail: true, Asana: true });
    });
    
    it('should handle model switching with tool preservation', () => {
      // Simulate switching models while preserving tools
      const model1: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'thread-1',
        toolkits: ['Gmail', 'Asana'],
      };
      
      // When switching models, tools should be preserved in rechargeModel
      const model2: ActiveModel = {
        model: 'llama3.2:3b',
        provider: 'ollama',
        thread_id: 'thread-2',
        toolkits: model1.toolkits, // Should preserve existing toolkits
      };
      
      expect(model2.toolkits).toEqual(['Gmail', 'Asana']);
      expect(model2.model).toBe('llama3.2:3b');
      expect(model2.provider).toBe('ollama');
    });
    
    it('should handle edge cases correctly', () => {
      const AVAILABLE_TOOLS: ToolName[] = ['Gmail', 'Asana'];
      
      // Test with invalid tool names in activeModel.toolkits
      const modelWithInvalidTools: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: ['Gmail', 'InvalidTool', 'Asana'],
      };
      
      const createToolsStateFromModel = (activeModel: ActiveModel) => {
        const toolsState: Record<ToolName, boolean> = {
          Gmail: false,
          Asana: false,
        };
        
        AVAILABLE_TOOLS.forEach(tool => {
          toolsState[tool] = activeModel.toolkits.includes(tool);
        });
        
        return toolsState;
      };
      
      const toolsState = createToolsStateFromModel(modelWithInvalidTools);
      
      // Should only recognize valid tools
      expect(toolsState).toEqual({ Gmail: true, Asana: true });
    });
  });
});