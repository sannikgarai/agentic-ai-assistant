"""
Document parser.

Detects supported document types and extracts basic text
and metadata from PDFs and images.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


@dataclass
class ParsedPage:
    """Represents one parsed document page."""

    page_number: int
    text: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert page to dictionary."""

        return {
            "page_number": self.page_number,
            "text": self.text,
            "metadata": self.metadata,
        }


@dataclass
class ParsedDocument:
    """Structured representation of a parsed document."""

    file_path: str
    filename: str
    extension: str
    document_type: str
    pages: list[ParsedPage] = field(
        default_factory=list
    )
    text: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @property
    def requires_ocr(self) -> bool:
        """Return whether OCR is required."""

        return bool(
            self.metadata.get(
                "requires_ocr",
                False,
            )
        )

    @property
    def page_count(self) -> int:
        """Return number of pages."""

        return len(self.pages)

    def to_dict(self) -> dict[str, Any]:
        """Convert parsed document to dictionary."""

        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "extension": self.extension,
            "document_type": self.document_type,
            "pages": [
                page.to_dict()
                for page in self.pages
            ],
            "text": self.text,
            "metadata": self.metadata,
        }


class DocumentParser:
    """Parse supported documents."""

    @staticmethod
    def is_supported(
        filename: str | Path,
    ) -> bool:
        """Check whether a file extension is supported."""

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        return extension in SUPPORTED_EXTENSIONS

    @staticmethod
    def get_extension(
        filename: str | Path,
    ) -> str:
        """Return normalized file extension."""

        return (
            Path(filename)
            .suffix
            .lower()
        )

    def parse(
        self,
        file_path: str | Path,
    ) -> ParsedDocument:
        """Parse a document from disk."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {path}"
            )

        extension = self.get_extension(path)

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"Document is empty: {path.name}"
            )

        if extension == ".pdf":
            return self._parse_pdf(path)

        return self._parse_image(path)

    def parse_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """Parse document bytes."""

        if not content:
            raise ValueError(
                "Document content is empty."
            )

        extension = self.get_extension(
            filename
        )

        if extension not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported document type: {extension}"
            )

        if extension == ".pdf":
            return self._parse_pdf_bytes(
                content,
                filename,
            )

        return self._parse_image_bytes(
            content,
            filename,
        )

    def _parse_pdf(
        self,
        path: Path,
    ) -> ParsedDocument:
        """Parse a PDF document."""

        pages: list[ParsedPage] = []

        try:
            with pymupdf.open(
                str(path)
            ) as document:

                pdf_metadata = dict(
                    document.metadata or {}
                )

                page_count = len(
                    document
                )

                for index, page in enumerate(
                    document,
                    start=1,
                ):
                    text = (
                        page.get_text(
                            "text"
                        )
                        or ""
                    ).strip()

                    pages.append(
                        ParsedPage(
                            page_number=index,
                            text=text,
                            metadata={
                                "page_number": index,
                                "has_text": bool(
                                    text
                                ),
                            },
                        )
                    )

        except Exception as exc:
            raise ValueError(
                f"Unable to parse PDF "
                f"'{path.name}': {exc}"
            ) from exc

        full_text = self._combine_page_text(
            pages
        )

        pages_requiring_ocr = [
            page.page_number
            for page in pages
            if not page.text.strip()
        ]

        requires_ocr = bool(
            pages_requiring_ocr
        )

        return ParsedDocument(
            file_path=str(
                path.resolve()
            ),
            filename=path.name,
            extension=".pdf",
            document_type="pdf",
            pages=pages,
            text=full_text,
            metadata={
                **pdf_metadata,
                "page_count": page_count,
                "requires_ocr": requires_ocr,
                "pages_requiring_ocr": (
                    pages_requiring_ocr
                ),
                "text_page_count": (
                    page_count
                    - len(pages_requiring_ocr)
                ),
                "size_bytes": path.stat().st_size,
            },
        )

    def _parse_pdf_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """Parse PDF bytes."""

        pages: list[ParsedPage] = []

        try:
            with pymupdf.open(
                stream=content,
                filetype="pdf",
            ) as document:

                pdf_metadata = dict(
                    document.metadata or {}
                )

                page_count = len(
                    document
                )

                for index, page in enumerate(
                    document,
                    start=1,
                ):
                    text = (
                        page.get_text(
                            "text"
                        )
                        or ""
                    ).strip()

                    pages.append(
                        ParsedPage(
                            page_number=index,
                            text=text,
                            metadata={
                                "page_number": index,
                                "has_text": bool(
                                    text
                                ),
                            },
                        )
                    )

        except Exception as exc:
            raise ValueError(
                f"Unable to parse PDF "
                f"'{filename}': {exc}"
            ) from exc

        full_text = self._combine_page_text(
            pages
        )

        pages_requiring_ocr = [
            page.page_number
            for page in pages
            if not page.text.strip()
        ]

        return ParsedDocument(
            file_path=filename,
            filename=filename,
            extension=".pdf",
            document_type="pdf",
            pages=pages,
            text=full_text,
            metadata={
                **pdf_metadata,
                "page_count": page_count,
                "requires_ocr": bool(
                    pages_requiring_ocr
                ),
                "pages_requiring_ocr": (
                    pages_requiring_ocr
                ),
                "text_page_count": (
                    page_count
                    - len(pages_requiring_ocr)
                ),
                "size_bytes": len(content),
            },
        )

    def _parse_image(
        self,
        path: Path,
    ) -> ParsedDocument:
        """Create a parsed representation of an image."""

        extension = path.suffix.lower()

        if extension not in IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image type: "
                f"{extension}"
            )

        size_bytes = path.stat().st_size

        return ParsedDocument(
            file_path=str(
                path.resolve()
            ),
            filename=path.name,
            extension=extension,
            document_type="image",
            pages=[
                ParsedPage(
                    page_number=1,
                    text="",
                    metadata={
                        "page_number": 1,
                        "has_text": False,
                    },
                )
            ],
            text="",
            metadata={
                "requires_ocr": True,
                "pages_requiring_ocr": [1],
                "page_count": 1,
                "size_bytes": size_bytes,
            },
        )

    def _parse_image_bytes(
        self,
        content: bytes,
        filename: str,
    ) -> ParsedDocument:
        """Create a parsed representation from image bytes."""

        extension = self.get_extension(
            filename
        )

        if extension not in IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image type: "
                f"{extension}"
            )

        return ParsedDocument(
            file_path=filename,
            filename=filename,
            extension=extension,
            document_type="image",
            pages=[
                ParsedPage(
                    page_number=1,
                    text="",
                    metadata={
                        "page_number": 1,
                        "has_text": False,
                    },
                )
            ],
            text="",
            metadata={
                "requires_ocr": True,
                "pages_requiring_ocr": [1],
                "page_count": 1,
                "size_bytes": len(content),
            },
        )

    @staticmethod
    def _combine_page_text(
        pages: list[ParsedPage],
    ) -> str:
        """Combine non-empty page text."""

        return "\n\n".join(
            page.text
            for page in pages
            if page.text.strip()
        )