"""
OCR engine.

Uses Tesseract OCR through pytesseract for scanned documents
and images.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pymupdf
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

from ..core.config import settings


class OCREngine:
    """Tesseract-based OCR engine."""

    DEFAULT_LANGUAGES = {
        "en": "eng",
        "bn": "ben",
        "hi": "hin",
        "or": "ori",
        "as": "asm",
    }

    TESSERACT_LANGUAGES = {
        "eng",
        "ben",
        "hin",
        "ori",
        "asm",
    }

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    def __init__(
        self,
        tesseract_cmd: str | None = None,
    ):
        command = (
            tesseract_cmd
            or shutil.which("tesseract")
        )

        if command:
            pytesseract.pytesseract.tesseract_cmd = (
                command
            )

        self.tesseract_cmd = (
            pytesseract.pytesseract.tesseract_cmd
        )

        self._verify_tesseract()

    # ======================================================
    # TESSERACT CHECK
    # ======================================================

    def _verify_tesseract(self) -> None:
        """
        Check whether Tesseract is available.

        Initialization does not fail if Tesseract is
        unavailable. Actual OCR operations will raise
        a clear RuntimeError.
        """

        try:
            pytesseract.get_tesseract_version()
            self.available = True
        except Exception:
            self.available = False

    # ======================================================
    # PROCESS DOCUMENT
    # ======================================================

    def process(
        self,
        file_path: str | Path,
        language: str = "en",
    ) -> dict[str, Any]:
        """
        Run OCR on an image or PDF.
        """

        path = Path(file_path)

        self._validate_file(path)

        language_code = self._resolve_language(
            language
        )

        self._ensure_tesseract()

        extension = path.suffix.lower()

        if extension == ".pdf":
            return self._process_pdf(
                path,
                language_code,
            )

        if extension in self.SUPPORTED_EXTENSIONS:
            return self._process_image(
                path,
                language_code,
            )

        raise ValueError(
            f"Unsupported OCR file type: "
            f"{extension}"
        )

    # ======================================================
    # EXTRACT TEXT
    # ======================================================

    def extract_text(
        self,
        file_path: str | Path,
        language: str = "en",
    ) -> str:
        """
        Extract OCR text only.
        """

        result = self.process(
            file_path=file_path,
            language=language,
        )

        return str(
            result.get(
                "text",
                "",
            )
        )

    # ======================================================
    # PROCESS PIL IMAGE
    # ======================================================

    def process_image(
        self,
        image: Image.Image,
        language: str = "en",
        preprocess: bool = True,
    ) -> str:
        """
        Run OCR directly on a PIL image.
        """

        if image is None:
            raise ValueError(
                "Image cannot be None."
            )

        language_code = self._resolve_language(
            language
        )

        self._ensure_tesseract()

        working_image = image.convert(
            "RGB"
        )

        if preprocess:
            working_image = self._preprocess_image(
                working_image
            )

        text = pytesseract.image_to_string(
            working_image,
            lang=language_code,
        )

        return text.strip()

    # ======================================================
    # AVAILABLE LANGUAGES
    # ======================================================

    def get_available_languages(
        self,
    ) -> list[str]:
        """
        Return languages currently available
        in the installed Tesseract environment.
        """

        try:
            languages = (
                pytesseract.get_languages(
                    config=""
                )
            )

            return sorted(languages)

        except Exception:
            return []

    # ======================================================
    # APPLICATION LANGUAGES
    # ======================================================

    def get_supported_languages(
        self,
    ) -> dict[str, str]:
        """
        Return application language mappings.
        """

        return dict(
            self.DEFAULT_LANGUAGES
        )

    # ======================================================
    # IMAGE OCR
    # ======================================================

    def _process_image(
        self,
        path: Path,
        language: str,
    ) -> dict[str, Any]:
        """
        OCR an image file.
        """

        try:
            with Image.open(path) as image:
                image.load()

                width, height = image.size

                text = self.process_image(
                    image,
                    language=language,
                    preprocess=True,
                )

        except Exception as exc:
            raise RuntimeError(
                f"OCR failed for image "
                f"'{path.name}': {exc}"
            ) from exc

        return {
            "success": True,
            "file_path": str(
                path.resolve()
            ),
            "text": text,
            "language": language,
            "width": width,
            "height": height,
            "page_count": 1,
            "pages": [
                {
                    "page_number": 1,
                    "text": text,
                }
            ],
            "method": "tesseract",
        }

    # ======================================================
    # PDF OCR
    # ======================================================

    def _process_pdf(
        self,
        path: Path,
        language: str,
    ) -> dict[str, Any]:
        """
        OCR each page of a PDF.

        PyMuPDF renders each page into an image before
        sending it to Tesseract.
        """

        pages: list[dict[str, Any]] = []
        all_text: list[str] = []

        try:
            with pymupdf.open(
                str(path)
            ) as document:

                page_count = len(
                    document
                )

                for index, page in enumerate(
                    document,
                    start=1,
                ):
                    pixmap = page.get_pixmap(
                        matrix=pymupdf.Matrix(
                            2,
                            2,
                        ),
                        alpha=False,
                    )

                    image = Image.frombytes(
                        "RGB",
                        (
                            pixmap.width,
                            pixmap.height,
                        ),
                        pixmap.samples,
                    )

                    try:
                        text = self.process_image(
                            image,
                            language=language,
                            preprocess=True,
                        )
                    finally:
                        image.close()

                    page_result = {
                        "page_number": index,
                        "text": text,
                        "width": pixmap.width,
                        "height": pixmap.height,
                    }

                    pages.append(
                        page_result
                    )

                    if text:
                        all_text.append(
                            text
                        )

        except Exception as exc:
            raise RuntimeError(
                f"OCR failed for PDF "
                f"'{path.name}': {exc}"
            ) from exc

        return {
            "success": True,
            "file_path": str(
                path.resolve()
            ),
            "text": "\n\n".join(
                all_text
            ),
            "pages": pages,
            "page_count": page_count,
            "language": language,
            "method": "tesseract",
        }

    # ======================================================
    # IMAGE PREPROCESSING
    # ======================================================

    @staticmethod
    def _preprocess_image(
        image: Image.Image,
    ) -> Image.Image:
        """
        Perform lightweight image preprocessing
        before OCR.
        """

        processed = image.convert(
            "L"
        )

        processed = processed.filter(
            ImageFilter.SHARPEN
        )

        processed = ImageEnhance.Contrast(
            processed
        ).enhance(1.5)

        return processed

    # ======================================================
    # VALIDATION
    # ======================================================

    def _validate_file(
        self,
        path: Path,
    ) -> None:
        """
        Validate OCR input file.
        """

        if not path.exists():
            raise FileNotFoundError(
                f"File not found: {path}"
            )

        if not path.is_file():
            raise ValueError(
                f"Path is not a file: {path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported OCR file type: "
                f"{extension}"
            )

        if path.stat().st_size == 0:
            raise ValueError(
                f"File is empty: {path.name}"
            )

    # ======================================================
    # TESSERACT AVAILABILITY
    # ======================================================

    def _ensure_tesseract(self) -> None:
        """
        Ensure Tesseract is available.
        """

        if not self.available:
            raise RuntimeError(
                "Tesseract OCR is not available. "
                "Please install Tesseract and make "
                "sure it is available in PATH."
            )

    # ======================================================
    # RESOLVE LANGUAGE
    # ======================================================

    def _resolve_language(
        self,
        language: str,
    ) -> str:
        """
        Convert application language codes to
        Tesseract language codes.

        Supports:
            en
            bn
            hi
            or
            as

        and combinations such as:
            eng+ben
            eng+hin
        """

        if not language:
            language = str(
                getattr(
                    settings,
                    "default_language",
                    "en",
                )
            )

        language = (
            language
            .strip()
            .lower()
        )

        if language in self.DEFAULT_LANGUAGES:
            return self.DEFAULT_LANGUAGES[
                language
            ]

        if "+" in language:
            languages = [
                item.strip()
                for item in language.split("+")
                if item.strip()
            ]

            if not languages:
                return "eng"

            resolved = []

            for item in languages:
                if item in self.DEFAULT_LANGUAGES:
                    resolved.append(
                        self.DEFAULT_LANGUAGES[
                            item
                        ]
                    )
                elif (
                    item
                    in self.TESSERACT_LANGUAGES
                ):
                    resolved.append(item)
                else:
                    raise ValueError(
                        f"Unsupported OCR language: "
                        f"{item}"
                    )

            return "+".join(
                dict.fromkeys(resolved)
            )

        if language in self.TESSERACT_LANGUAGES:
            return language

        return "eng"