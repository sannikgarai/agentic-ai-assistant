"""
PDF text extraction.

Uses PyMuPDF to extract text page by page while preserving
page-level metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf


@dataclass
class ExtractedPage:
    """Text extracted from one PDF page."""

    page_number: int
    text: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class ExtractedDocument:
    """Complete extracted PDF document."""

    file_path: str
    filename: str
    pages: list[ExtractedPage] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def full_text(self) -> str:
        """Return all extracted text."""

        return "\n\n".join(
            page.text
            for page in self.pages
            if page.text.strip()
        )


class PDFExtractor:
    """Extract text from PDF files."""

    def extract(
        self,
        file_path: str | Path,
    ) -> ExtractedDocument:
        """Extract text from a PDF."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {path}"
            )

        pages: list[ExtractedPage] = []

        with pymupdf.open(str(path)) as document:
            document_metadata = (
                dict(document.metadata or {})
            )

            for index, page in enumerate(
                document,
                start=1,
            ):
                text = page.get_text(
                    "text"
                )

                pages.append(
                    ExtractedPage(
                        page_number=index,
                        text=text or "",
                        metadata={
                            "page_number": index,
                        },
                    )
                )

        return ExtractedDocument(
            file_path=str(path.resolve()),
            filename=path.name,
            pages=pages,
            metadata=document_metadata,
        )

    def extract_bytes(
        self,
        content: bytes,
        filename: str = "document.pdf",
    ) -> ExtractedDocument:
        """Extract text from PDF bytes."""

        pages: list[ExtractedPage] = []

        with pymupdf.open(
            stream=content,
            filetype="pdf",
        ) as document:
            document_metadata = (
                dict(document.metadata or {})
            )

            for index, page in enumerate(
                document,
                start=1,
            ):
                text = page.get_text(
                    "text"
                )

                pages.append(
                    ExtractedPage(
                        page_number=index,
                        text=text or "",
                        metadata={
                            "page_number": index,
                        },
                    )
                )

        return ExtractedDocument(
            file_path=filename,
            filename=filename,
            pages=pages,
            metadata=document_metadata,
        )