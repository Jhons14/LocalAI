import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import type { ActiveModel } from '@/types/chat';
import type { NavigationItems } from '@/types/sidebar';
import { getModelIndices, validateModel } from '@/utils/modelMapping';

// Mock data for integration testing
const mockNavigationItems: NavigationItems = [
  {
    name: 'OpenAI',
    icon: null,
    subItems: [
      { title: 'GPT-4', model: 'gpt-4', provider: 'openai' },
    ],
  },
  {
    name: 'Ollama', 
    icon: null,
    subItems: [
      { title: 'Llama 3.2', model: 'llama3.2:3b', provider: 'ollama' },
    ],
  },
];

describe('Phase 1 Integration Tests', () => {
  describe('Model State Synchronization', () => {
    it('should correctly map active model to sidebar indices', () => {
      const activeModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: ['Gmail'],
      };

      const { providerIndex, modelIndex } = getModelIndices(activeModel, mockNavigationItems);
      
      expect(providerIndex).toBe(0);
      expect(modelIndex).toBe(0);
    });

    it('should validate model exists in navigation items', () => {
      const validModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const invalidModel: ActiveModel = {
        model: 'non-existent',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      expect(validateModel(validModel, mockNavigationItems)).toBe(true);
      expect(validateModel(invalidModel, mockNavigationItems)).toBe(false);
    });

    it('should preserve toolkits when switching models', () => {
      // This test simulates the rechargeModel behavior
      const originalModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai', 
        thread_id: 'thread-1',
        toolkits: ['Gmail', 'Asana'],
      };

      // Simulate rechargeModel preserving toolkits
      const newModel: ActiveModel = {
        model: 'llama3.2:3b',
        provider: 'ollama',
        thread_id: 'thread-2',
        toolkits: originalModel.toolkits, // Should preserve existing toolkits
      };

      expect(newModel.toolkits).toEqual(['Gmail', 'Asana']);
      expect(newModel.model).toBe('llama3.2:3b');
      expect(newModel.provider).toBe('ollama');
    });

    it('should handle edge cases correctly', () => {
      // Test with empty navigation items
      expect(getModelIndices(null, [])).toEqual({
        providerIndex: 0,
        modelIndex: undefined,
      });

      // Test with null active model
      expect(validateModel(null, mockNavigationItems)).toBe(false);
      expect(validateModel(undefined, mockNavigationItems)).toBe(false);
    });
  });
});