import { describe, it, expect } from 'vitest';
import {
  getModelIndices,
  getModelFromIndices,
  validateModel,
  getDefaultModel,
} from '../modelMapping';
import type { ActiveModel } from '@/types/chat';
import type { NavigationItems } from '@/types/sidebar';

// Mock navigation items for testing
const mockNavigationItems: NavigationItems = [
  {
    name: 'OpenAI',
    icon: null,
    subItems: [
      { title: 'GPT-4', model: 'gpt-4', provider: 'openai' },
      { title: 'GPT-3.5', model: 'gpt-3.5-turbo', provider: 'openai' },
    ],
  },
  {
    name: 'Anthropic',
    icon: null,
    subItems: [
      { title: 'Claude 3', model: 'claude-3-opus', provider: 'anthropic' },
    ],
  },
  {
    name: 'Google',
    icon: null,
    subItems: [
      { title: 'Gemini Pro', model: 'gemini-pro', provider: 'google' },
    ],
  },
  {
    name: 'Ollama',
    icon: null,
    subItems: [
      { title: 'Llama 3.2', model: 'llama3.2:3b', provider: 'ollama' },
      { title: 'Qwen 2.5', model: 'qwen2.5:3b', provider: 'ollama' },
    ],
  },
];

describe('modelMapping utilities', () => {
  describe('getModelIndices', () => {
    it('should return correct indices for existing model', () => {
      const activeModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = getModelIndices(activeModel, mockNavigationItems);
      
      expect(result).toEqual({
        providerIndex: 0,
        modelIndex: 0,
      });
    });

    it('should return correct indices for Ollama model', () => {
      const activeModel: ActiveModel = {
        model: 'qwen2.5:3b',
        provider: 'ollama',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = getModelIndices(activeModel, mockNavigationItems);
      
      expect(result).toEqual({
        providerIndex: 3,
        modelIndex: 1,
      });
    });

    it('should return default indices for non-existing model', () => {
      const activeModel: ActiveModel = {
        model: 'non-existing-model',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = getModelIndices(activeModel, mockNavigationItems);
      
      expect(result).toEqual({
        providerIndex: 0,
        modelIndex: undefined,
      });
    });

    it('should handle null/undefined activeModel', () => {
      const result1 = getModelIndices(null, mockNavigationItems);
      const result2 = getModelIndices(undefined, mockNavigationItems);
      
      expect(result1).toEqual({ providerIndex: 0, modelIndex: undefined });
      expect(result2).toEqual({ providerIndex: 0, modelIndex: undefined });
    });

    it('should handle empty navigation items', () => {
      const activeModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = getModelIndices(activeModel, []);
      
      expect(result).toEqual({ providerIndex: 0, modelIndex: undefined });
    });
  });

  describe('getModelFromIndices', () => {
    it('should return correct model config for valid indices', () => {
      const result = getModelFromIndices(0, 0, mockNavigationItems);
      
      expect(result).toEqual({
        title: 'GPT-4',
        model: 'gpt-4',
        provider: 'openai',
      });
    });

    it('should return null for invalid provider index', () => {
      const result = getModelFromIndices(99, 0, mockNavigationItems);
      expect(result).toBeNull();
    });

    it('should return null for undefined model index', () => {
      const result = getModelFromIndices(0, undefined, mockNavigationItems);
      expect(result).toBeNull();
    });

    it('should return null for invalid model index', () => {
      const result = getModelFromIndices(0, 99, mockNavigationItems);
      expect(result).toBeNull();
    });
  });

  describe('validateModel', () => {
    it('should return true for valid model', () => {
      const activeModel: ActiveModel = {
        model: 'gpt-4',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = validateModel(activeModel, mockNavigationItems);
      expect(result).toBe(true);
    });

    it('should return false for invalid model', () => {
      const activeModel: ActiveModel = {
        model: 'non-existing',
        provider: 'openai',
        thread_id: 'test-thread',
        toolkits: [],
      };

      const result = validateModel(activeModel, mockNavigationItems);
      expect(result).toBe(false);
    });

    it('should return false for null activeModel', () => {
      const result = validateModel(null, mockNavigationItems);
      expect(result).toBe(false);
    });
  });

  describe('getDefaultModel', () => {
    it('should return first Ollama model if available', () => {
      const result = getDefaultModel(mockNavigationItems);
      
      expect(result).toEqual({
        title: 'Llama 3.2',
        model: 'llama3.2:3b',
        provider: 'ollama',
      });
    });

    it('should return first available model if no Ollama', () => {
      const itemsWithoutOllama = mockNavigationItems.slice(0, 3);
      const result = getDefaultModel(itemsWithoutOllama);
      
      expect(result).toEqual({
        title: 'GPT-4',
        model: 'gpt-4',
        provider: 'openai',
      });
    });

    it('should return null for empty navigation items', () => {
      const result = getDefaultModel([]);
      expect(result).toBeNull();
    });

    it('should return null if no providers have models', () => {
      const emptyProviders = [
        { name: 'OpenAI', icon: null, subItems: [] },
        { name: 'Ollama', icon: null, subItems: [] },
      ];
      
      const result = getDefaultModel(emptyProviders);
      expect(result).toBeNull();
    });
  });
});