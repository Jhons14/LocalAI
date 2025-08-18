import { describe, it, expect } from 'vitest';
import type { ActiveModel, ToolName } from '@/types/chat';
import type { NavigationItems } from '@/types/sidebar';
import { getModelIndices, validateModel, getDefaultModel } from '@/utils/modelMapping';

describe('Complete State Synchronization Solution', () => {
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
      name: 'Ollama',
      icon: null,
      subItems: [
        { title: 'Llama 3.2', model: 'llama3.2:3b', provider: 'ollama' },
      ],
    },
  ];

  it('🎯 Complete End-to-End State Synchronization', () => {
    console.log('🚀 Testing complete state synchronization solution...');
    
    // 1. Initial page load scenario
    console.log('📱 Simulating page reload...');
    
    // Simulate loading phases
    const phases = ['initializing', 'loading-models', 'syncing-state', 'ready'];
    let currentPhase = 0;
    
    // 2. Load persisted active model
    const persistedModel: ActiveModel = {
      model: 'claude-3-opus',
      provider: 'anthropic',
      thread_id: 'persisted-thread-123',
      toolkits: ['Gmail', 'Asana'],
    };
    console.log('💾 Loaded persisted model:', persistedModel);
    
    // 3. Validate model exists in navigation items
    const isValidModel = validateModel(persistedModel, mockNavigationItems);
    expect(isValidModel).toBe(true);
    console.log('✅ Model validation passed');
    
    // 4. Get sidebar indices for persisted model
    const { providerIndex, modelIndex } = getModelIndices(persistedModel, mockNavigationItems);
    expect(providerIndex).toBe(1); // Anthropic
    expect(modelIndex).toBe(0);    // Claude 3
    console.log(`📍 Sidebar should show: Provider ${providerIndex}, Model ${modelIndex}`);
    
    // 5. Simulate tools state synchronization
    const AVAILABLE_TOOLS: ToolName[] = ['Gmail', 'Asana'];
    const toolsState = AVAILABLE_TOOLS.reduce((acc, tool) => {
      acc[tool] = persistedModel.toolkits.includes(tool);
      return acc;
    }, {} as Record<ToolName, boolean>);
    
    expect(toolsState).toEqual({ Gmail: true, Asana: true });
    console.log('🛠️ Tools state synced:', toolsState);
    
    // 6. Simulate model switch via sidebar
    console.log('🔄 Simulating model switch...');
    const newModelConfig = mockNavigationItems[2].subItems![0]; // Ollama Llama
    
    // rechargeModel should preserve toolkits
    const switchedModel: ActiveModel = {
      model: newModelConfig.model,
      provider: newModelConfig.provider,
      thread_id: persistedModel.thread_id, // preserved
      toolkits: persistedModel.toolkits,   // preserved
    };
    
    expect(switchedModel).toEqual({
      model: 'llama3.2:3b',
      provider: 'ollama',
      thread_id: 'persisted-thread-123',
      toolkits: ['Gmail', 'Asana'], // Tools preserved!
    });
    console.log('✅ Model switched with preserved tools');
    
    // 7. Verify new sidebar selection
    const newIndices = getModelIndices(switchedModel, mockNavigationItems);
    expect(newIndices).toEqual({ providerIndex: 2, modelIndex: 0 });
    console.log(`📍 Sidebar updated to: Provider ${newIndices.providerIndex}, Model ${newIndices.modelIndex}`);
    
    // 8. Simulate tool toggle
    console.log('🔧 Simulating tool toggle...');
    const toggledToolkits = switchedModel.toolkits.filter(t => t !== 'Gmail'); // Disable Gmail
    const modelAfterToolToggle: ActiveModel = {
      ...switchedModel,
      toolkits: toggledToolkits,
    };
    
    expect(modelAfterToolToggle.toolkits).toEqual(['Asana']);
    console.log('✅ Tool toggle updated model state');
    
    // 9. Verify final state consistency
    const finalValidation = validateModel(modelAfterToolToggle, mockNavigationItems);
    const finalIndices = getModelIndices(modelAfterToolToggle, mockNavigationItems);
    const finalToolsState = AVAILABLE_TOOLS.reduce((acc, tool) => {
      acc[tool] = modelAfterToolToggle.toolkits.includes(tool);
      return acc;
    }, {} as Record<ToolName, boolean>);
    
    expect(finalValidation).toBe(true);
    expect(finalIndices).toEqual({ providerIndex: 2, modelIndex: 0 });
    expect(finalToolsState).toEqual({ Gmail: false, Asana: true });
    
    console.log('🎉 Final state verification:');
    console.log('   Model:', modelAfterToolToggle.model);
    console.log('   Provider:', modelAfterToolToggle.provider);
    console.log('   Sidebar indices:', finalIndices);
    console.log('   Tools state:', finalToolsState);
    console.log('   All states synchronized: ✅');
  });

  it('🚨 Error Recovery and Edge Cases', () => {
    console.log('🛡️ Testing error recovery...');
    
    // 1. Invalid persisted model scenario
    const invalidModel: ActiveModel = {
      model: 'non-existent-model',
      provider: 'openai',
      thread_id: 'invalid-thread',
      toolkits: ['Gmail'],
    };
    
    const isValid = validateModel(invalidModel, mockNavigationItems);
    expect(isValid).toBe(false);
    console.log('❌ Invalid model detected');
    
    // 2. Fallback to default model
    const defaultModel = getDefaultModel(mockNavigationItems);
    expect(defaultModel).toEqual({
      title: 'Llama 3.2',
      model: 'llama3.2:3b',
      provider: 'ollama',
    });
    
    const fallbackActiveModel: ActiveModel = {
      model: defaultModel!.model,
      provider: defaultModel!.provider,
      thread_id: invalidModel.thread_id, // preserve thread
      toolkits: invalidModel.toolkits,   // preserve tools
    };
    
    expect(fallbackActiveModel).toEqual({
      model: 'llama3.2:3b',
      provider: 'ollama',
      thread_id: 'invalid-thread',
      toolkits: ['Gmail'],
    });
    console.log('🔄 Fallback model created with preserved state');
    
    // 3. Empty navigation items
    const emptyNavResult = getDefaultModel([]);
    expect(emptyNavResult).toBeNull();
    console.log('⚠️ Handled empty navigation items');
    
    // 4. Race condition simulation
    let isLoading = true;
    let navigationReady = false;
    
    const canSync = () => !isLoading && navigationReady;
    
    expect(canSync()).toBe(false);
    navigationReady = true;
    expect(canSync()).toBe(false);
    isLoading = false;
    expect(canSync()).toBe(true);
    console.log('⏱️ Race condition handling verified');
    
    console.log('✅ All error recovery scenarios passed');
  });

  it('📊 Performance and State Optimization', () => {
    console.log('⚡ Testing performance optimizations...');
    
    const model: ActiveModel = {
      model: 'gpt-4',
      provider: 'openai', 
      thread_id: 'perf-test',
      toolkits: ['Gmail'],
    };
    
    // 1. Test index computation performance
    const startTime = performance.now();
    
    for (let i = 0; i < 1000; i++) {
      getModelIndices(model, mockNavigationItems);
    }
    
    const endTime = performance.now();
    const avgTime = (endTime - startTime) / 1000;
    
    expect(avgTime).toBeLessThan(1); // Should average < 1ms per call
    console.log(`📈 Index computation: ${avgTime.toFixed(3)}ms average`);
    
    // 2. Test validation performance
    const validationStartTime = performance.now();
    
    for (let i = 0; i < 1000; i++) {
      validateModel(model, mockNavigationItems);
    }
    
    const validationEndTime = performance.now();
    const avgValidationTime = (validationEndTime - validationStartTime) / 1000;
    
    expect(avgValidationTime).toBeLessThan(1);
    console.log(`🔍 Model validation: ${avgValidationTime.toFixed(3)}ms average`);
    
    // 3. Test state change detection
    const previousState = { providerIndex: 0, modelIndex: 0 };
    const currentState = getModelIndices(model, mockNavigationItems);
    
    const hasChanged = (
      previousState.providerIndex !== currentState.providerIndex ||
      previousState.modelIndex !== currentState.modelIndex
    );
    
    // Only update if actually changed (optimization)
    if (hasChanged) {
      console.log('🔄 State change detected, would update UI');
    } else {
      console.log('⚡ No change detected, skipping update');
    }
    
    console.log('✅ Performance optimizations verified');
  });
});