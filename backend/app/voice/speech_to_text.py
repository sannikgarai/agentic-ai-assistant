"""
Speech-to-text processing using Whisper.

The implementation is intentionally lazy-loaded so importing the
application does not immediately load the Whisper model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.core.config import settings


@dataclass
class TranscriptionResult:
    """Result returned by speech-to-text."""

    text: str
    language: str | None = None
    duration: float | None = None
    segments: list[dict[str, Any]] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "text": self.text,
            "language": self.language,
            "duration": self.duration,
            "segments": self.segments,
            "metadata": self.metadata,
        }


class SpeechToText:
    """Whisper-based speech recognition service."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
    ):
        self.model_name = (
            model_name
            or settings.whisper_model
        )

        self.device = device

        self._model = None

    def _load_model(self):
        """Load Whisper model lazily."""

        if self._model is not None:
            return self._model

        try:
            import whisper
        except ImportError as exc:
            raise RuntimeError(
                "Whisper is not installed. "
                "Install the required Whisper package."
            ) from exc

        load_kwargs: dict[str, Any] = {}

        if self.device:
            load_kwargs["device"] = self.device

        self._model = whisper.load_model(
            self.model_name,
            **load_kwargs,
        )

        return self._model

    def transcribe(
        self,
        audio_path: str | Path,
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscriptionResult:
        """
        Transcribe an audio file.

        Parameters:
            audio_path:
                Path to audio/video file.

            language:
                Optional language code such as:
                en, bn, hi, or.

            task:
                'transcribe' keeps the spoken language.
                'translate' translates speech to English.
        """

        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Audio path is not a file: {path}"
            )

        model = self._load_model()

        options: dict[str, Any] = {
            "task": task,
            "fp16": False,
        }

        if language:
            options["language"] = self._normalize_language(
                language
            )

        try:
            result = model.transcribe(
                str(path),
                **options,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Speech transcription failed: {exc}"
            ) from exc

        segments = []

        for segment in result.get(
            "segments",
            [],
        ):
            segments.append(
                {
                    "id": segment.get("id"),
                    "start": segment.get("start"),
                    "end": segment.get("end"),
                    "text": segment.get(
                        "text",
                        "",
                    ).strip(),
                }
            )

        duration = None

        if segments:
            duration = max(
                float(segment["end"])
                for segment in segments
                if segment.get("end") is not None
            )

        return TranscriptionResult(
            text=result.get(
                "text",
                "",
            ).strip(),
            language=result.get(
                "language"
            ),
            duration=duration,
            segments=segments,
            metadata={
                "model": self.model_name,
                "task": task,
                "audio_file": path.name,
            },
        )

    def transcribe_bytes(
        self,
        audio_bytes: bytes,
        filename: str,
        language: str | None = None,
        task: str = "transcribe",
    ) -> TranscriptionResult:
        """Transcribe audio supplied as bytes."""

        if not audio_bytes:
            raise ValueError(
                "Audio data is empty."
            )

        suffix = Path(filename).suffix

        if not suffix:
            suffix = ".wav"

        temp_dir = Path(
            settings.audio_dir
            if hasattr(settings, "audio_dir")
            else settings.temp_dir
        )

        temp_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_file = (
            temp_dir
            / f"voice_input{suffix}"
        )

        try:
            temp_file.write_bytes(
                audio_bytes
            )

            return self.transcribe(
                temp_file,
                language=language,
                task=task,
            )

        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass

    @staticmethod
    def _normalize_language(
        language: str,
    ) -> str:
        """Normalize common language codes."""

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