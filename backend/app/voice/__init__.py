"""
Voice processing package.

Provides:
- Speech-to-text
- Text-to-speech
- Language detection
- Translation
"""

from backend.app.voice.language_detector import (
    LanguageDetector,
    LanguageDetectionResult,
)
from backend.app.voice.speech_to_text import (
    SpeechToText,
    TranscriptionResult,
)
from backend.app.voice.text_to_speech import (
    TextToSpeech,
    SpeechResult,
)
from backend.app.voice.translator import (
    Translator,
    TranslationResult,
)

__all__ = [
    "SpeechToText",
    "TranscriptionResult",
    "TextToSpeech",
    "SpeechResult",
    "LanguageDetector",
    "LanguageDetectionResult",
    "Translator",
    "TranslationResult",
]