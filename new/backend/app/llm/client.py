"""
Google Gemini LLM client.

Provides synchronous and asynchronous methods for
communicating with Google's Gemini API.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from google import genai
from google.genai import types

from backend.app.core.config import settings
from backend.app.core.logging import get_logger


logger = get_logger(__name__)


# ============================================================
# GEMINI CLIENT
# ============================================================

class GeminiClient:
    """
    Client for interacting with Google Gemini.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.gemini_model

        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        if not self.model:
            raise ValueError(
                "GEMINI_MODEL is not configured."
            )

        self.client = genai.Client(
            api_key=self.api_key
        )

        # Retry only temporary server errors.
        self.max_retries = 2

        print("=" * 60)
        print("GEMINI CLIENT INITIALIZED")
        print(f"Model: {self.model}")
        print(
            f"API key configured: "
            f"{bool(self.api_key)}"
        )
        print("=" * 60)

        logger.info(
            "Gemini client initialized with model: %s",
            self.model,
        )

    # ========================================================
    # RESPONSE EXTRACTION
    # ========================================================

    @staticmethod
    def _extract_text(
        response: Any,
    ) -> str:
        """
        Safely extract generated text from a Gemini response.
        """

        text = getattr(
            response,
            "text",
            None,
        )

        if isinstance(text, str) and text.strip():
            return text.strip()

        candidates = getattr(
            response,
            "candidates",
            None,
        )

        if not candidates:
            return ""

        parts_text: list[str] = []

        for candidate in candidates:
            content = getattr(
                candidate,
                "content",
                None,
            )

            if not content:
                continue

            parts = getattr(
                content,
                "parts",
                None,
            )

            if not parts:
                continue

            for part in parts:
                part_text = getattr(
                    part,
                    "text",
                    None,
                )

                if (
                    isinstance(part_text, str)
                    and part_text.strip()
                ):
                    parts_text.append(
                        part_text.strip()
                    )

        return "\n".join(parts_text)

    # ========================================================
    # ERROR DETECTION
    # ========================================================

    @staticmethod
    def _is_temporary_server_error(
        exc: Exception,
    ) -> bool:
        """
        Check whether an exception appears to be
        a temporary Gemini server availability error.
        """

        error_text = str(exc).upper()

        return (
            "503" in error_text
            or "UNAVAILABLE" in error_text
            or "SERVICE UNAVAILABLE" in error_text
        )

    @staticmethod
    def _is_rate_limit_error(
        exc: Exception,
    ) -> bool:
        """
        Check whether an exception represents
        a quota or rate-limit error.
        """

        error_text = str(exc).upper()

        return (
            "429" in error_text
            or "RESOURCE_EXHAUSTED" in error_text
            or "QUOTA" in error_text
            or "RATE LIMIT" in error_text
        )

    @staticmethod
    def _friendly_error_message(
        exc: Exception,
    ) -> str:
        """
        Convert common Gemini errors into
        application-level messages.
        """

        if GeminiClient._is_rate_limit_error(exc):
            return (
                "Gemini API rate limit or quota "
                "was exceeded. Please wait before "
                "trying again."
            )

        if GeminiClient._is_temporary_server_error(exc):
            return (
                "Gemini is temporarily unavailable. "
                "Please try again shortly."
            )

        return f"Gemini request failed: {exc}"

    # ========================================================
    # CONFIGURATION
    # ========================================================

    @staticmethod
    def _build_config(
        *,
        temperature: float,
        max_output_tokens: int,
        system_instruction: str | None = None,
        response_mime_type: str | None = None,
    ) -> types.GenerateContentConfig:
        """
        Build Gemini generation configuration.
        """

        config_kwargs: dict[str, Any] = {
            "temperature": temperature,
            "max_output_tokens": max_output_tokens,
        }

        if system_instruction:
            config_kwargs["system_instruction"] = (
                system_instruction
            )

        if response_mime_type:
            config_kwargs["response_mime_type"] = (
                response_mime_type
            )

        return types.GenerateContentConfig(
            **config_kwargs
        )

    # ========================================================
    # RETRY DELAY
    # ========================================================

    @staticmethod
    def _retry_delay(
        attempt: int,
    ) -> int:
        """
        Return exponential retry delay.
        """

        return 2 ** attempt

    # ========================================================
    # SYNCHRONOUS TEXT GENERATION
    # ========================================================

    def generate(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate text synchronously.
        """

        self._validate_prompt(prompt)

        config = self._build_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                )

                text = self._extract_text(
                    response
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return text

            except Exception as exc:
                last_exception = exc

                if self._is_rate_limit_error(exc):
                    logger.error(
                        "Gemini quota/rate limit reached."
                    )
                    break

                if (
                    self._is_temporary_server_error(
                        exc
                    )
                    and attempt < self.max_retries
                ):
                    delay = self._retry_delay(
                        attempt
                    )

                    logger.warning(
                        "Gemini temporarily unavailable. "
                        "Retrying in %s seconds.",
                        delay,
                    )

                    time.sleep(delay)
                    continue

                break

        if last_exception is None:
            raise RuntimeError(
                "Gemini generation failed."
            )

        logger.exception(
            "Gemini synchronous generation failed."
        )

        raise RuntimeError(
            self._friendly_error_message(
                last_exception
            )
        ) from last_exception

    # ========================================================
    # ASYNCHRONOUS TEXT GENERATION
    # ========================================================

    async def generate_async(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate text asynchronously.
        """

        self._validate_prompt(prompt)

        config = self._build_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = (
                    await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                )

                text = self._extract_text(
                    response
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return text

            except Exception as exc:
                last_exception = exc

                if self._is_rate_limit_error(exc):
                    logger.error(
                        "Gemini quota/rate limit reached."
                    )
                    break

                if (
                    self._is_temporary_server_error(
                        exc
                    )
                    and attempt < self.max_retries
                ):
                    delay = self._retry_delay(
                        attempt
                    )

                    logger.warning(
                        "Gemini temporarily unavailable. "
                        "Retrying in %s seconds.",
                        delay,
                    )

                    await asyncio.sleep(delay)
                    continue

                break

        if last_exception is None:
            raise RuntimeError(
                "Gemini asynchronous generation failed."
            )

        logger.exception(
            "Gemini asynchronous generation failed."
        )

        raise RuntimeError(
            self._friendly_error_message(
                last_exception
            )
        ) from last_exception

    # ========================================================
    # ASYNCHRONOUS MULTIMODAL GENERATION
    # ========================================================

    async def generate_multimodal_async(
        self,
        prompt: str,
        *,
        image_bytes: bytes,
        mime_type: str,
        system_instruction: str | None = None,
        temperature: float = 0.2,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate a response using text plus an image.

        The image is supplied directly to Gemini as binary data.
        """

        self._validate_prompt(prompt)

        if not isinstance(
            image_bytes,
            bytes,
        ):
            raise TypeError(
                "image_bytes must be bytes."
            )

        if not image_bytes:
            raise ValueError(
                "image_bytes cannot be empty."
            )

        if not isinstance(
            mime_type,
            str,
        ) or not mime_type.strip():
            raise ValueError(
                "mime_type must be provided."
            )

        config = self._build_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

        image_part = types.Part.from_bytes(
            data=image_bytes,
            mime_type=mime_type,
        )

        contents = [
            prompt,
            image_part,
        ]

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = (
                    await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=contents,
                        config=config,
                    )
                )

                text = self._extract_text(
                    response
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty response."
                    )

                return text

            except Exception as exc:
                last_exception = exc

                if self._is_rate_limit_error(exc):
                    logger.error(
                        "Gemini quota/rate limit reached "
                        "during multimodal generation."
                    )
                    break

                if (
                    self._is_temporary_server_error(
                        exc
                    )
                    and attempt < self.max_retries
                ):
                    delay = self._retry_delay(
                        attempt
                    )

                    logger.warning(
                        "Gemini temporarily unavailable "
                        "during image processing. "
                        "Retrying in %s seconds.",
                        delay,
                    )

                    await asyncio.sleep(delay)
                    continue

                break

        if last_exception is None:
            raise RuntimeError(
                "Gemini multimodal generation failed."
            )

        logger.exception(
            "Gemini multimodal generation failed."
        )

        raise RuntimeError(
            self._friendly_error_message(
                last_exception
            )
        ) from last_exception

    # ========================================================
    # SYNCHRONOUS JSON GENERATION
    # ========================================================

    def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate structured JSON synchronously.
        """

        self._validate_prompt(prompt)

        config = self._build_json_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = (
                    self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                )

                text = self._extract_text(
                    response
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty JSON response."
                    )

                return text

            except Exception as exc:
                last_exception = exc

                if self._is_rate_limit_error(exc):
                    break

                if (
                    self._is_temporary_server_error(
                        exc
                    )
                    and attempt < self.max_retries
                ):
                    time.sleep(
                        self._retry_delay(attempt)
                    )
                    continue

                break

        if last_exception is None:
            raise RuntimeError(
                "Gemini JSON generation failed."
            )

        logger.exception(
            "Gemini synchronous JSON generation failed."
        )

        raise RuntimeError(
            self._friendly_error_message(
                last_exception
            )
        ) from last_exception

    # ========================================================
    # ASYNCHRONOUS JSON GENERATION
    # ========================================================

    async def generate_json_async(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        temperature: float = 0.1,
        max_output_tokens: int = 4096,
    ) -> str:
        """
        Generate structured JSON asynchronously.
        """

        self._validate_prompt(prompt)

        config = self._build_json_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
        )

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):
            try:
                response = (
                    await self.client.aio.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=config,
                    )
                )

                text = self._extract_text(
                    response
                )

                if not text:
                    raise RuntimeError(
                        "Gemini returned an empty JSON response."
                    )

                return text

            except Exception as exc:
                last_exception = exc

                if self._is_rate_limit_error(exc):
                    break

                if (
                    self._is_temporary_server_error(
                        exc
                    )
                    and attempt < self.max_retries
                ):
                    await asyncio.sleep(
                        self._retry_delay(attempt)
                    )
                    continue

                break

        if last_exception is None:
            raise RuntimeError(
                "Gemini asynchronous JSON generation failed."
            )

        logger.exception(
            "Gemini asynchronous JSON generation failed."
        )

        raise RuntimeError(
            self._friendly_error_message(
                last_exception
            )
        ) from last_exception

    # ========================================================
    # SIMPLE CHAT
    # ========================================================

    async def chat(
        self,
        message: str,
        *,
        history: list[dict[str, str]] | None = None,
        system_instruction: str | None = None,
    ) -> str:
        """
        Simple asynchronous chat interface.
        """

        self._validate_message(message)

        prompt_parts: list[str] = []

        if history:
            for item in history:
                role = item.get(
                    "role",
                    "user",
                )

                content = item.get(
                    "content",
                    "",
                )

                if not content:
                    continue

                prompt_parts.append(
                    f"{role.upper()}: {content}"
                )

        prompt_parts.append(
            f"USER: {message}"
        )

        prompt = "\n\n".join(
            prompt_parts
        )

        return await self.generate_async(
            prompt=prompt,
            system_instruction=system_instruction,
        )

    # ========================================================
    # VALIDATION HELPERS
    # ========================================================

    @staticmethod
    def _validate_prompt(
        prompt: str,
    ) -> None:
        """
        Validate a generation prompt.
        """

        if not isinstance(
            prompt,
            str,
        ):
            raise TypeError(
                "Prompt must be a string."
            )

        if not prompt.strip():
            raise ValueError(
                "Prompt cannot be empty."
            )

    @staticmethod
    def _validate_message(
        message: str,
    ) -> None:
        """
        Validate a chat message.
        """

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "Message must be a string."
            )

        if not message.strip():
            raise ValueError(
                "Message cannot be empty."
            )

    # ========================================================
    # JSON CONFIGURATION
    # ========================================================

    @staticmethod
    def _build_json_config(
        *,
        temperature: float,
        max_output_tokens: int,
        system_instruction: str | None = None,
    ) -> types.GenerateContentConfig:
        """
        Build configuration for JSON generation.
        """

        json_instruction = (
            "Return only valid JSON. "
            "Do not include Markdown code fences, "
            "explanations, or additional text."
        )

        if system_instruction:
            combined_instruction = (
                f"{system_instruction}\n\n"
                f"{json_instruction}"
            )
        else:
            combined_instruction = (
                json_instruction
            )

        return GeminiClient._build_config(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=combined_instruction,
            response_mime_type="application/json",
        )


# ============================================================
# CLIENT FACTORY
# ============================================================

def get_gemini_client() -> GeminiClient:
    """
    Create and return a Gemini client.
    """

    return GeminiClient()