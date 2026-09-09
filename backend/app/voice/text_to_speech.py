"""
Text-to-speech processing.

Uses edge-tts when available.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.app.core.config import settings


@dataclass
class SpeechResult:
    """Result returned by text-to-speech."""

    audio_path: str
    text: str
    language: str
    voice: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "audio_path": self.audio_path,
            "text": self.text,
            "language": self.language,
            "voice": self.voice,
            "metadata": self.metadata,
        }


class TextToSpeech:
    """Text-to-speech service."""

    DEFAULT_VOICES = {
        "en": "en-IN-NeerjaNeural",
        "bn": "bn-IN-TanishaaNeural",
        "hi": "hi-IN-SwaraNeural",
        "or": "en-IN-NeerjaNeural",
        "as": "en-IN-NeerjaNeural",
    }

    def __init__(
        self,
        output_dir: str | Path | None = None,
    ):
        if output_dir is not None:
            self.output_dir = Path(
                output_dir
            )
        else:
            self.output_dir = Path(
                settings.audio_dir
            )

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

    def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: str | None = None,
        filename: str | None = None,
    ) -> SpeechResult:
        """Convert text to an audio file."""

        text = text.strip()

        if not text:
            raise ValueError(
                "Text for speech synthesis cannot be empty."
            )

        language = self._normalize_language(
            language
        )

        selected_voice = (
            voice
            or self.DEFAULT_VOICES.get(
                language,
                self.DEFAULT_VOICES["en"],
            )
        )

        if filename:
            output_name = filename
        else:
            output_name = (
                f"tts_{self._safe_name(text)}.mp3"
            )

        output_path = (
            self.output_dir
            / output_name
        )

        try:
            self._synthesize_sync(
                text=text,
                voice=selected_voice,
                output_path=output_path,
            )
        except ImportError as exc:
            raise RuntimeError(
                "edge-tts is not installed. "
                "Install it with: pip install edge-tts"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"Text-to-speech failed: {exc}"
            ) from exc

        return SpeechResult(
            audio_path=str(
                output_path
            ),
            text=text,
            language=language,
            voice=selected_voice,
            metadata={
                "format": "mp3",
            },
        )

    def _synthesize_sync(
        self,
        text: str,
        voice: str,
        output_path: Path,
    ) -> None:
        """Run asynchronous edge-tts synthesis."""

        try:
            import edge_tts
        except ImportError:
            raise

        async def generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
            )

            await communicate.save(
                str(output_path)
            )

        try:
            asyncio.run(
                generate()
            )
        except RuntimeError as exc:
            if "asyncio.run()" in str(exc):
                loop = asyncio.new_event_loop()

                try:
                    loop.run_until_complete(
                        generate()
                    )
                finally:
                    loop.close()
            else:
                raise

    async def synthesize_async(
        self,
        text: str,
        language: str = "en",
        voice: str | None = None,
        filename: str | None = None,
    ) -> SpeechResult:
        """Asynchronously synthesize speech."""

        text = text.strip()

        if not text:
            raise ValueError(
                "Text for speech synthesis cannot be empty."
            )

        language = self._normalize_language(
            language
        )

        selected_voice = (
            voice
            or self.DEFAULT_VOICES.get(
                language,
                self.DEFAULT_VOICES["en"],
            )
        )

        output_name = (
            filename
            or f"tts_{self._safe_name(text)}.mp3"
        )

        output_path = (
            self.output_dir
            / output_name
        )

        try:
            import edge_tts
        except ImportError as exc:
            raise RuntimeError(
                "edge-tts is not installed. "
                "Install it with: pip install edge-tts"
            ) from exc

        communicate = edge_tts.Communicate(
            text=text,
            voice=selected_voice,
        )

        await communicate.save(
            str(output_path)
        )

        return SpeechResult(
            audio_path=str(
                output_path
            ),
            text=text,
            language=language,
            voice=selected_voice,
            metadata={
                "format": "mp3",
            },
        )

    @staticmethod
    def _normalize_language(
        language: str,
    ) -> str:
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
        }

        normalized = (
            language.strip().lower()
        )

        return mapping.get(
            normalized,
            normalized,
        )

    @staticmethod
    def _safe_name(
        text: str,
        max_length: int = 30,
    ) -> str:
        """Create a safe filename component."""

        import hashlib
        import re

        digest = hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()[:12]

        clean = re.sub(
            r"[^a-zA-Z0-9]+",
            "_",
            text,
        ).strip("_")

        clean = clean[:max_length]

        return (
            f"{clean}_{digest}"
            if clean
            else digest
        )