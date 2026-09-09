import pytest


def test_voice_modules_import():
    from app.voice import (
        speech_to_text,
        text_to_speech,
        language_detector,
        translator,
    )

    modules = [
        speech_to_text,
        text_to_speech,
        language_detector,
        translator,
    ]

    for module in modules:
        assert module is not None


def test_voice_configuration_exists():
    from app.core.config import settings

    assert hasattr(settings, "whisper_model")
    assert hasattr(settings, "default_language")


def test_whisper_model_configured():
    from app.core.config import settings

    assert settings.whisper_model


def test_default_language_configured():
    from app.core.config import settings

    assert settings.default_language


def test_speech_to_text_module():
    from app.voice import speech_to_text

    assert speech_to_text is not None


def test_text_to_speech_module():
    from app.voice import text_to_speech

    assert text_to_speech is not None


def test_language_detector_module():
    from app.voice import language_detector

    assert language_detector is not None


def test_translator_module():
    from app.voice import translator

    assert translator is not None


def test_audio_directory_configured():
    from app.core.config import settings

    assert settings.audio_dir is not None