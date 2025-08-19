"""
Prompt management utilities for the LocalAI Chat API
"""
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PromptLoader:
    """Load and manage system prompts from files"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(__file__).parent
        self._cache = {}
    
    def load_prompt(self, filename: str) -> str:
        """Load a prompt from file with caching"""
        if filename in self._cache:
            return self._cache[filename]
        
        try:
            file_path = self.prompts_dir / filename
            if not file_path.exists():
                logger.warning(f"Prompt file not found: {file_path}")
                return ""
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self._cache[filename] = content
            logger.debug(f"Loaded prompt from {filename}")
            return content
            
        except Exception as e:
            logger.error(f"Error loading prompt {filename}: {e}")
            return ""
    
    def build_system_message(self, memories_str: str = "", tool_manager=None, extract_schemas_func=None) -> str:
        """Build complete system message from prompt templates"""
        base_msg = self.load_prompt("base_system_message.txt")
        
        if tool_manager and extract_schemas_func:
            # Try to extract dynamic tool schemas using provided function
            dynamic_schemas = extract_schemas_func(tool_manager)
            logger.info(f"Extracted tool schemas: {dynamic_schemas[:200]}..." if len(dynamic_schemas) > 200 else f"Extracted tool schemas: {dynamic_schemas}")
            
            if dynamic_schemas:
                # Use dynamic schemas
                tool_instructions = self.load_prompt("tool_usage_instructions.txt")
                tool_instructions = tool_instructions.format(dynamic_schemas=dynamic_schemas)
            else:
                # Use fallback
                tool_instructions = self.load_prompt("tool_usage_fallback.txt")
            
            base_msg += tool_instructions
        
        if memories_str:
            memory_section = self.load_prompt("memory_section.txt")
            base_msg += memory_section.format(memories_str=memories_str)
        
        return base_msg

# Global instance
prompt_loader = PromptLoader()