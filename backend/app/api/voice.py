"""
Voice API routes.

Handles:
- Speech-to-text
- Text-to-speech
- Language detection
- Translation
"""

from __future__ import annotations

from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
)

from backend.app.core.logging import get_logger
from backend.app.core.security import (
    get_current_user,
    get_user_id,
)
from backend.app.voice.speech_to_text import (
    SpeechToText,
)


# ---------------------------------------------------------------------
# Router and logger
# ---------------------------------------------------------------------

router = APIRouter()

logger = get_logger(__name__)


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

MAX_AUDIO_SIZE = 25 * 1024 * 1024

SUPPORTED_AUDIO_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/m4a",
    "audio/x-m4a",
}


# ---------------------------------------------------------------------
# Speech-to-Text
# ---------------------------------------------------------------------

@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "auto",
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Transcribe uploaded audio using Whisper.
    """

    user_id = get_user_id(user)

    filename = (
        audio.filename or ""
    ).strip()

    requested_language = (
        language.strip().lower()
        if language
        else "auto"
    )

    # -----------------------------------------------------------------
    # Validate filename
    # -----------------------------------------------------------------

    if not filename:
        return {
            "success": False,
            "message": "Audio filename is missing.",
            "filename": None,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
        }

    logger.info(
        "Audio transcription request | user=%s | "
        "filename=%s | language=%s",
        user_id,
        filename,
        requested_language,
    )

    # -----------------------------------------------------------------
    # Validate content type when available
    # -----------------------------------------------------------------

    content_type = (
        audio.content_type or ""
    ).strip().lower()

    if (
        content_type
        and content_type not in SUPPORTED_AUDIO_TYPES
        and not content_type.startswith("audio/")
    ):
        return {
            "success": False,
            "message": (
                "Unsupported audio format."
            ),
            "filename": filename,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
            "metadata": {
                "status": "unsupported_audio_type",
                "content_type": content_type,
            },
        }

    # -----------------------------------------------------------------
    # Read uploaded audio
    # -----------------------------------------------------------------

    try:
        audio_bytes = await audio.read()

    except Exception as exc:
        logger.exception(
            "Failed to read audio file | user=%s | filename=%s",
            user_id,
            filename,
        )

        return {
            "success": False,
            "message": "Unable to read the uploaded audio.",
            "filename": filename,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
            "metadata": {
                "status": "file_read_error",
                "error_type": type(exc).__name__,
            },
        }

    # -----------------------------------------------------------------
    # Validate audio
    # -----------------------------------------------------------------

    if not audio_bytes:
        return {
            "success": False,
            "message": "Audio data is empty.",
            "filename": filename,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
            "metadata": {
                "status": "empty_file",
            },
        }

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        max_size_mb = (
            MAX_AUDIO_SIZE / (1024 * 1024)
        )

        return {
            "success": False,
            "message": (
                f"Audio file is too large. "
                f"Maximum allowed size is "
                f"{max_size_mb:.0f} MB."
            ),
            "filename": filename,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
            "metadata": {
                "status": "file_too_large",
                "file_size": len(audio_bytes),
                "max_file_size": MAX_AUDIO_SIZE,
            },
        }

    # -----------------------------------------------------------------
    # Whisper transcription
    # -----------------------------------------------------------------

    try:
        speech_to_text = SpeechToText()

        transcription = (
            speech_to_text.transcribe_bytes(
                audio_bytes=audio_bytes,
                filename=filename,
                language=(
                    None
                    if requested_language == "auto"
                    else requested_language
                ),
                task="transcribe",
            )
        )

        transcript = (
            transcription.text.strip()
        )

        detected_language = (
            transcription.language
            or requested_language
        )

        logger.info(
            "Audio transcription completed | user=%s | "
            "language=%s | text_length=%d",
            user_id,
            detected_language,
            len(transcript),
        )

        return {
            "success": True,
            "message": (
                "Audio transcribed successfully."
            ),
            "filename": filename,
            "language": detected_language,
            "user_id": user_id,
            "transcript": transcript,
            "text": transcript,
            "duration": transcription.duration,
            "segments": transcription.segments,
            "metadata": {
                **(
                    transcription.metadata
                    or {}
                ),
                "status": "completed",
                "file_size": len(audio_bytes),
                "content_type": content_type,
            },
        }

    except Exception as exc:
        logger.exception(
            "Whisper transcription failed | user=%s | filename=%s",
            user_id,
            filename,
        )

        return {
            "success": False,
            "message": (
                "Unable to transcribe the audio."
            ),
            "filename": filename,
            "language": requested_language,
            "user_id": user_id,
            "transcript": None,
            "text": "",
            "metadata": {
                "status": "transcription_error",
                "error_type": type(exc).__name__,
            },
        }


# ---------------------------------------------------------------------
# Text-to-Speech
# ---------------------------------------------------------------------

@router.post("/speak")
async def speak_text(
    request: dict[str, Any],
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Convert text to speech.

    Uses the project's TextToSpeech implementation
    when available.
    """

    user_id = get_user_id(user)

    text = str(
        request.get("text", "")
    ).strip()

    language = str(
        request.get(
            "language",
            "en",
        )
    ).strip().lower()

    if not text:
        return {
            "success": False,
            "message": "Text is required.",
            "language": language,
            "text": "",
            "user_id": user_id,
        }

    try:
        from backend.app.voice.text_to_speech import (
            TextToSpeech,
        )

        text_to_speech = TextToSpeech()

        # Support common method names used by TTS implementations.
        if hasattr(
            text_to_speech,
            "synthesize",
        ):
            result = await text_to_speech.synthesize(
                text=text,
                language=language,
            )

        elif hasattr(
            text_to_speech,
            "generate",
        ):
            result = await text_to_speech.generate(
                text=text,
                language=language,
            )

        else:
            raise RuntimeError(
                "TextToSpeech implementation does not "
                "provide a supported synthesis method."
            )

        logger.info(
            "Text-to-speech completed | user=%s | language=%s",
            user_id,
            language,
        )

        if isinstance(result, dict):
            return {
                "success": True,
                "message": (
                    "Speech generated successfully."
                ),
                "language": language,
                "text": text,
                "user_id": user_id,
                **result,
            }

        return {
            "success": True,
            "message": (
                "Speech generated successfully."
            ),
            "language": language,
            "text": text,
            "user_id": user_id,
            "audio": result,
        }

    except Exception as exc:
        logger.exception(
            "Text-to-speech failed | user=%s",
            user_id,
        )

        return {
            "success": False,
            "message": (
                "Unable to generate speech."
            ),
            "language": language,
            "text": text,
            "user_id": user_id,
            "metadata": {
                "status": "tts_error",
                "error_type": type(exc).__name__,
            },
        }


# ---------------------------------------------------------------------
# Language Detection
# ---------------------------------------------------------------------

@router.post("/detect-language")
async def detect_language(
    request: dict[str, Any],
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Detect the language of supplied text.
    """

    user_id = get_user_id(user)

    text = str(
        request.get("text", "")
    ).strip()

    if not text:
        return {
            "success": False,
            "message": "Text is required.",
            "language": None,
            "text": "",
            "user_id": user_id,
        }

    try:
        from backend.app.voice.language_detector import (
            LanguageDetector,
        )

        detector = LanguageDetector()

        result = detector.detect(text)

        if isinstance(result, dict):
            return {
                **result,
                "success": True,
                "user_id": user_id,
            }

        return {
            "success": True,
            "language": result,
            "text": text,
            "user_id": user_id,
        }

    except Exception as exc:
        logger.exception(
            "Language detection failed | user=%s",
            user_id,
        )

        return {
            "success": False,
            "message": (
                "Unable to detect the language."
            ),
            "language": None,
            "text": text,
            "user_id": user_id,
            "metadata": {
                "status": "language_detection_error",
                "error_type": type(exc).__name__,
            },
        }


# ---------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------

@router.post("/translate")
async def translate_text(
    request: dict[str, Any],
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Translate text between supported languages.

    Uses the project's Translator implementation
    when available.
    """

    user_id = get_user_id(user)

    text = str(
        request.get("text", "")
    ).strip()

    source_language = str(
        request.get(
            "source_language",
            "auto",
        )
    ).strip().lower()

    target_language = str(
        request.get(
            "target_language",
            "en",
        )
    ).strip().lower()

    if not text:
        return {
            "success": False,
            "message": "Text is required.",
            "text": "",
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": "",
            "user_id": user_id,
        }

    if not target_language:
        return {
            "success": False,
            "message": (
                "Target language is required."
            ),
            "text": text,
            "source_language": source_language,
            "target_language": "",
            "translated_text": "",
            "user_id": user_id,
        }

    try:
        from backend.app.voice.translator import (
            Translator,
        )

        translator = Translator()

        # -------------------------------------------------------------
        # Support common translator interfaces.
        # -------------------------------------------------------------

        if hasattr(
            translator,
            "translate",
        ):
            result = await translator.translate(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )

        elif hasattr(
            translator,
            "translate_text",
        ):
            result = await translator.translate_text(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )

        else:
            raise RuntimeError(
                "Translator implementation does not "
                "provide a supported translation method."
            )

        logger.info(
            "Translation completed | user=%s | "
            "%s -> %s",
            user_id,
            source_language,
            target_language,
        )

        if isinstance(result, dict):
            return {
                "success": True,
                "message": (
                    "Text translated successfully."
                ),
                "text": text,
                "source_language": source_language,
                "target_language": target_language,
                "user_id": user_id,
                **result,
            }

        translated_text = str(result)

        return {
            "success": True,
            "message": (
                "Text translated successfully."
            ),
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": translated_text,
            "user_id": user_id,
        }

    except Exception as exc:
        logger.exception(
            "Translation failed | user=%s | %s -> %s",
            user_id,
            source_language,
            target_language,
        )

        return {
            "success": False,
            "message": (
                "Unable to translate the text."
            ),
            "text": text,
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": "",
            "user_id": user_id,
            "metadata": {
                "status": "translation_error",
                "error_type": type(exc).__name__,
            },
        }