"""
Multilingual translation using the configured LLM.

Gemini is used instead of maintaining separate translation
models for every supported regional language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.llm.client import GeminiClient


@dataclass
class TranslationResult:
    """Translation result."""

    source_text: str
    translated_text: str
    source_language: str
    target_language: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "source_text": self.source_text,
            "translated_text": self.translated_text,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "metadata": self.metadata,
        }


class Translator:
    """Gemini-based multilingual translator."""

    def __init__(
        self,
        client: GeminiClient | None = None,
    ):
        self.client = (
            client
            or GeminiClient()
        )

    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
    ) -> TranslationResult:
        """Translate text into the target language."""

        text = text.strip()

        if not text:
            raise ValueError(
                "Text to translate cannot be empty."
            )

        target_language = (
            self.normalize_language(
                target_language
            )
        )

        source_language = (
            self.normalize_language(
                source_language
            )
            if source_language != "auto"
            else "auto"
        )

        if (
            source_language != "auto"
            and source_language
            == target_language
        ):
            return TranslationResult(
                source_text=text,
                translated_text=text,
                source_language=source_language,
                target_language=target_language,
                metadata={
                    "translated": False,
                    "reason": (
                        "Source and target languages are identical."
                    ),
                },
            )

        prompt = f"""
Translate the following text accurately.

Source language: {source_language}
Target language: {target_language}

Requirements:
- Preserve the original meaning.
- Do not add explanations.
- Do not summarize.
- Preserve names, numbers, dates, IDs, and important terminology.
- Use natural language appropriate for the target language.
- Return only the translated text.

Text:
{text}
"""

        try:
            translated = await self.client.generate_async(
                prompt=prompt
            )
        except Exception as exc:
            raise RuntimeError(
                f"Translation failed: {exc}"
            ) from exc

        translated = translated.strip()

        if not translated:
            raise RuntimeError(
                "Translation returned empty text."
            )

        return TranslationResult(
            source_text=text,
            translated_text=translated,
            source_language=source_language,
            target_language=target_language,
            metadata={
                "translated": True,
                "provider": "gemini",
            },
        )

    def translate_sync(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto",
    ) -> TranslationResult:
        """Synchronous translation wrapper."""

        import asyncio

        return asyncio.run(
            self.translate(
                text=text,
                target_language=target_language,
                source_language=source_language,
            )
        )

    @staticmethod
    def normalize_language(
        language: str,
    ) -> str:
        """Normalize language names and codes."""

        mapping = {
            "english": "en",
            "eng": "en",

            "bengali": "bn",
            "bangla": "bn",
            "ben": "bn",

            "hindi": "hi",
            "hin": "hi",

            "odia": "or",
            "oriya": "or",
            "ori": "or",

            "assamese": "as",
            "asm": "as",

            "tamil": "ta",
            "tam": "ta",

            "telugu": "te",
            "tel": "te",

            "kannada": "kn",
            "kan": "kn",

            "malayalam": "ml",
            "mal": "ml",

            "marathi": "mr",
            "mar": "mr",

            "gujarati": "gu",
            "guj": "gu",

            "punjabi": "pa",
            "pan": "pa",

            "urdu": "ur",
            "urd": "ur",
        }

        normalized = (
            language.strip().lower()
        )

        return mapping.get(
            normalized,
            normalized,
        )