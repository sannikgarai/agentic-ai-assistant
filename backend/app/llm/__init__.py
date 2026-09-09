
"""
LLM package for the Agentic AI Assistant.

This package provides:
- Gemini client integration
- Prompt management
- LLM response parsing
"""

from backend.app.llm.client import GeminiClient
from backend.app.llm.parser import (
    ParsedLLMResponse,
    parse_json_response,
    parse_llm_response,
)

__all__ = [
    "GeminiClient",
    "ParsedLLMResponse",
    "parse_json_response",
    "parse_llm_response",
]
