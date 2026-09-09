"""
Text cleaning utilities for RAG.

Normalizes whitespace and removes common PDF extraction noise
while preserving meaningful text.
"""

from __future__ import annotations

import re


class TextCleaner:
    """Clean extracted document text."""

    def clean(self, text: str) -> str:
        """Clean a complete text string."""

        if not text:
            return ""

        text = text.replace(
            "\r\n",
            "\n",
        )

        text = text.replace(
            "\r",
            "\n",
        )

        # Remove null characters.
        text = text.replace(
            "\x00",
            "",
        )

        # Join words broken by a line-ending hyphen.
        text = re.sub(
            r"(?<=\w)-\n(?=\w)",
            "",
            text,
        )

        # Normalize tabs.
        text = text.replace(
            "\t",
            " ",
        )

        # Collapse excessive spaces.
        text = re.sub(
            r"[ ]{2,}",
            " ",
            text,
        )

        # Keep paragraph structure but remove excessive blank lines.
        text = re.sub(
            r"\n[ ]*\n[ ]*\n+",
            "\n\n",
            text,
        )

        # Remove spaces around newlines.
        text = re.sub(
            r"[ ]+\n",
            "\n",
            text,
        )

        text = re.sub(
            r"\n[ ]+",
            "\n",
            text,
        )

        return text.strip()

    def clean_lines(
        self,
        lines: list[str],
    ) -> list[str]:
        """Clean individual lines."""

        cleaned: list[str] = []

        for line in lines:
            value = self.clean(line)

            if value:
                cleaned.append(value)

        return cleaned

    def normalize_for_search(
        self,
        text: str,
    ) -> str:
        """
        Normalize text for lexical comparison.

        Original text should still be stored separately.
        """

        cleaned = self.clean(text)

        return " ".join(
            cleaned.lower().split()
        )