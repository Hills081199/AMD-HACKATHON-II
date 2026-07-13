"""Factory for creating LLM clients."""

from typing import Type

from .base import LLMClientBase
from .gemini_client import GeminiClient


def get_llm_client() -> Type[LLMClientBase]:
    return GeminiClient
