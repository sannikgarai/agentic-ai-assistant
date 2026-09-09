"""
Language detection for text.

Uses langdetect when available and provides a lightweight
fallback for common Indian scripts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LanguageDetectionResult:
    """Language detection result."""

    language: str
    confidence: float
    detected_by: str
    alternatives: list[dict[str, Any]] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "language": self.language,
            "confidence": self.confidence,
            "detected_by": self.detected_by,
            "alternatives": self.alternatives,
        }


class LanguageDetector:
    """Detect language from text."""

    SCRIPT_RANGES = {
        "bn": (
            "\u0980",
            "\u09FF",
        ),
        "hi": (
            "\u0900",
            "\u097F",
        ),
        "or": (
            "\u0B00",
            "\u0B7F",
        ),
    }

    def detect(
        self,
        text: str,
    ) -> LanguageDetectionResult:
        """Detect the language of text."""

        if not text or not text.strip():
            return LanguageDetectionResult(
                language="unknown",
                confidence=0.0,
                detected_by="none",
            )

        text = text.strip()

        script_result = self._detect_script(
            text
        )

        if script_result:
            return script_result

        try:
            from langdetect import detect_langs

            detected = detect_langs(text)

            if not detected:
                raise ValueError(
                    "No language detected."
                )

            primary = detected[0]

            alternatives = [
                {
                    "language": item.lang,
                    "confidence": round(
                        item.prob,
                        4,
                    ),
                }
                for item in detected[:5]
            ]

            return LanguageDetectionResult(
                language=primary.lang,
                confidence=round(
                    primary.prob,
                    4,
                ),
                detected_by="langdetect",
                alternatives=alternatives,
            )

        except Exception:
            return self._fallback_latin(
                text
            )

    def detect_many(
        self,
        texts: list[str],
    ) -> list[LanguageDetectionResult]:
        """Detect languages for multiple texts."""

        return [
            self.detect(text)
            for text in texts
        ]

    def _detect_script(
        self,
        text: str,
    ) -> LanguageDetectionResult | None:
        """Detect common Indian scripts."""

        counts = {
            "bn": 0,
            "hi": 0,
            "or": 0,
        }

        for char in text:
            code = ord(char)

            if (
                0x0980
                <= code
                <= 0x09FF
            ):
                counts["bn"] += 1

            elif (
                0x0900
                <= code
                <= 0x097F
            ):
                counts["hi"] += 1

            elif (
                0x0B00
                <= code
                <= 0x0B7F
            ):
                counts["or"] += 1

        total = sum(
            counts.values()
        )

        if total == 0:
            return None

        language, count = max(
            counts.items(),
            key=lambda item: item[1],
        )

        if count == 0:
            return None

        confidence = count / total

        return LanguageDetectionResult(
            language=language,
            confidence=round(
                confidence,
                4,
            ),
            detected_by="unicode_script",
        )

    @staticmethod
    def _fallback_latin(
        text: str,
    ) -> LanguageDetectionResult:
        """
        Fallback when langdetect is unavailable.

        English is used as the safest default for Latin text.
        """

        return LanguageDetectionResult(
            language="en",
            confidence=0.50,
            detected_by="fallback",
        )