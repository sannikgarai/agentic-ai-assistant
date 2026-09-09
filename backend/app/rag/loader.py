
"""
PDF document loader.

Discovers PDF files from the government document directory
and loads their binary content and metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.app.core.config import GOVERNMENT_PDF_DIR


@dataclass
class PDFDocument:
    """Represents a loaded PDF document."""

    file_path: str
    filename: str
    category: str
    content: bytes
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert document metadata to a dictionary."""

        return {
            "file_path": self.file_path,
            "filename": self.filename,
            "category": self.category,
            "metadata": self.metadata,
        }


class PDFLoader:
    """Loads PDF files from disk."""

    def __init__(
        self,
        root_directory: str | Path | None = None,
    ):
        self.root_directory = Path(
            root_directory or GOVERNMENT_PDF_DIR
        )

    def discover(
        self,
        category: str | None = None,
    ) -> list[Path]:
        """
        Discover PDF files.

        If category is supplied, only that category directory
        is searched.
        """

        search_directory = self.root_directory

        if category:
            search_directory = (
                self.root_directory / category
            )

        if not search_directory.exists():
            return []

        return sorted(
            path
            for path in search_directory.rglob("*.pdf")
            if path.is_file()
        )

    def load(
        self,
        file_path: str | Path,
    ) -> PDFDocument:
        """Load a single PDF."""

        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"PDF file not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {path}"
            )

        if path.suffix.lower() != ".pdf":
            raise ValueError(
                f"Expected a PDF file, got: {path.suffix}"
            )

        content = path.read_bytes()

        category = self._get_category(path)

        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "file_size": path.stat().st_size,
            "category": category,
        }

        return PDFDocument(
            file_path=str(path.resolve()),
            filename=path.name,
            category=category,
            content=content,
            metadata=metadata,
        )

    def load_all(
        self,
        category: str | None = None,
    ) -> list[PDFDocument]:
        """Load all discovered PDFs."""

        documents: list[PDFDocument] = []

        for file_path in self.discover(category):
            try:
                documents.append(
                    self.load(file_path)
                )
            except Exception:
                # A single bad file should not stop ingestion.
                continue

        return documents

    def _get_category(
        self,
        path: Path,
    ) -> str:
        """Determine the category of a PDF."""

        try:
            relative_path = path.relative_to(
                self.root_directory
            )

            if len(relative_path.parts) > 1:
                return relative_path.parts[0]

        except ValueError:
            pass

        return "other"
