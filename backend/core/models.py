"""
Model providers and factory for creating LLM instances.
"""
from enum import Enum
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import SecretStr

from config.settings import get_settings

settings = get_settings()


class ModelProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ModelFactory:
    """Factory for creating language model instances."""

    @staticmethod
    def create_model(
        provider: ModelProvider,
        model_name: str,
        api_key: Optional[str] = None,
        temperature: float = settings.default_temperature,
        max_tokens: int = settings.default_max_tokens,
        streaming: bool = True
    ):
        """
        Create a language model based on provider.

        Args:
            provider: The LLM provider to use
            model_name: Name of the model
            api_key: API key for the provider (required for non-Ollama)
            temperature: Temperature for response generation
            max_tokens: Maximum tokens for response
            streaming: Whether to enable streaming

        Returns:
            A configured LangChain chat model instance

        Raises:
            ValueError: If provider is unsupported or API key is missing
        """

        if provider == ModelProvider.OPENAI:
            if not api_key:
                raise ValueError("API key required for OpenAI")
            return ChatOpenAI(
                model=model_name,
                timeout=settings.default_timeout,
                max_retries=2,
                api_key=SecretStr(api_key),
                streaming=streaming
            )

        elif provider == ModelProvider.OLLAMA:
            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=settings.ollama.base_url
            )

        elif provider == ModelProvider.ANTHROPIC:
            if not api_key:
                raise ValueError("API key required for Anthropic")
            return ChatAnthropic(
                model_name=model_name,
                temperature=temperature,
                api_key=SecretStr(api_key),
                streaming=streaming,
                timeout=settings.default_timeout,
                stop=None
            )

        elif provider == ModelProvider.GOOGLE:
            if not api_key:
                raise ValueError("API key required for Google")
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens,
                google_api_key=api_key,
                streaming=streaming
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")
