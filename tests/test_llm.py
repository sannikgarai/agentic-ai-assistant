import pytest


def test_llm_client_module_imports():
    from app.llm import client

    assert client is not None


def test_llm_prompts_module_imports():
    from app.llm import prompts

    assert prompts is not None


def test_llm_parser_module_imports():
    from app.llm import parser

    assert parser is not None


def test_gemini_configuration_exists():
    from app.core.config import settings

    assert hasattr(settings, "gemini_api_key")
    assert hasattr(settings, "gemini_model")


def test_gemini_model_has_value():
    from app.core.config import settings

    assert settings.gemini_model


def test_llm_client_can_be_created_without_network_call():
    from app.llm.client import GeminiClient

    client = GeminiClient()

    assert client is not None


def test_llm_prompt_module_has_content():
    from app.llm import prompts

    public_items = [
        name
        for name in dir(prompts)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0


def test_parser_module_has_content():
    from app.llm import parser

    public_items = [
        name
        for name in dir(parser)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0