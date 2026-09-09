"""
scripts/process_documents.py

Process uploaded documents.

Supported:
    PDF
    PNG
    JPG
    JPEG
    WEBP

Input:
    data/uploaded_documents/

Output:
    data/processed_documents/

Run from project root:

    python scripts/process_documents.py
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.core.config import settings


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("process_documents")


# ---------------------------------------------------------------------
# Supported extensions
# ---------------------------------------------------------------------

PDF_EXTENSIONS = {
    ".pdf",
}

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


# ---------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalize extracted text.
    """

    if not text:
        return ""

    lines = []

    for line in text.splitlines():

        line = " ".join(
            line.strip().split()
        )

        if line:
            lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------

def extract_pdf_text(
    file_path: Path,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Extract text from every PDF page.

    Returns:
        complete_text,
        page_details
    """

    page_details: list[dict[str, Any]] = []
    all_text: list[str] = []

    document = fitz.open(file_path)

    try:

        for page_number, page in enumerate(
            document,
            start=1,
        ):

            text = page.get_text(
                "text"
            )

            text = clean_text(text)

            page_details.append(
                {
                    "page": page_number,
                    "text": text,
                    "characters": len(text),
                }
            )

            if text:
                all_text.append(text)

    finally:
        document.close()

    return (
        "\n\n".join(all_text),
        page_details,
    )


# ---------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------

def ocr_image(
    image: Image.Image,
) -> str:
    """
    Extract text from an image using Tesseract.
    """

    if pytesseract is None:

        raise RuntimeError(
            "pytesseract is not installed.\n"
            "Install it with:\n"
            "pip install pytesseract"
        )

    try:

        text = pytesseract.image_to_string(
            image
        )

        return clean_text(text)

    except Exception as exc:

        raise RuntimeError(
            "Tesseract OCR failed. "
            "Make sure Tesseract is installed "
            "and available in PATH."
        ) from exc


# ---------------------------------------------------------------------
# Image processing
# ---------------------------------------------------------------------

def process_image(
    file_path: Path,
) -> tuple[str, list[dict[str, Any]]]:
    """
    Process an image document.
    """

    image = Image.open(
        file_path
    )

    try:

        image = image.convert("RGB")

        text = ocr_image(
            image
        )

    finally:

        image.close()

    page_details = [
        {
            "page": 1,
            "text": text,
            "characters": len(text),
        }
    ]

    return text, page_details


# ---------------------------------------------------------------------
# Document type
# ---------------------------------------------------------------------

def classify_document(
    file_path: Path,
) -> str:
    """
    Basic document classification from filename.
    """

    name = file_path.stem.lower()

    if "aadhaar" in name:
        return "identity"

    if "aadhar" in name:
        return "identity"

    if "pan" in name:
        return "identity"

    if "passport" in name:
        return "identity"

    if "income" in name:
        return "income_certificate"

    if "caste" in name:
        return "caste_certificate"

    if "certificate" in name:
        return "certificate"

    if "marksheet" in name:
        return "education"

    if "mark" in name:
        return "education"

    if "bank" in name:
        return "bank_document"

    if "address" in name:
        return "address_proof"

    return "other"


# ---------------------------------------------------------------------
# Process one document
# ---------------------------------------------------------------------

def process_document(
    file_path: Path,
) -> dict[str, Any]:
    """
    Process one uploaded document.
    """

    extension = file_path.suffix.lower()

    logger.info(
        "Processing: %s",
        file_path.name,
    )

    if extension in PDF_EXTENSIONS:

        text, pages = extract_pdf_text(
            file_path
        )

        extraction_method = "pdf_text"

    elif extension in IMAGE_EXTENSIONS:

        text, pages = process_image(
            file_path
        )

        extraction_method = "ocr"

    else:

        raise ValueError(
            f"Unsupported file type: {extension}"
        )

    document_type = classify_document(
        file_path
    )

    result = {
        "file_name": file_path.name,
        "file_path": str(
            file_path.relative_to(
                PROJECT_ROOT
            )
        ),
        "document_type": document_type,
        "mime_type": get_mime_type(
            extension
        ),
        "file_size": file_path.stat().st_size,
        "extraction_method": extraction_method,
        "text": text,
        "text_length": len(text),
        "pages": pages,
        "processed_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "status": "completed",
    }

    return result


# ---------------------------------------------------------------------
# MIME type
# ---------------------------------------------------------------------

def get_mime_type(
    extension: str,
) -> str:
    """
    Return basic MIME type.
    """

    mapping = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }

    return mapping.get(
        extension.lower(),
        "application/octet-stream",
    )


# ---------------------------------------------------------------------
# Save result
# ---------------------------------------------------------------------

def save_processed_document(
    result: dict[str, Any],
) -> Path:
    """
    Save extracted document information as JSON.
    """

    output_dir = Path(
        settings.processed_document_dir
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    original_name = Path(
        result["file_name"]
    ).stem

    output_file = (
        output_dir
        / f"{original_name}.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            result,
            file,
            ensure_ascii=False,
            indent=2,
        )

    return output_file


# ---------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------

def process_all_documents() -> None:
    """
    Process every supported document in the upload directory.
    """

    input_dir = Path(
        settings.uploaded_document_dir
    )

    if not input_dir.exists():

        logger.warning(
            "Upload directory does not exist: %s",
            input_dir,
        )

        input_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        return

    files = sorted(
        file
        for file in input_dir.rglob("*")
        if file.is_file()
        and file.suffix.lower()
        in (
            PDF_EXTENSIONS
            | IMAGE_EXTENSIONS
        )
    )

    if not files:

        logger.info(
            "No documents found in %s",
            input_dir,
        )

        return

    logger.info(
        "Found %d documents.",
        len(files),
    )

    successful = 0
    failed = 0

    for file_path in files:

        try:

            result = process_document(
                file_path
            )

            output_path = (
                save_processed_document(
                    result
                )
            )

            successful += 1

            logger.info(
                "Processed successfully: %s",
                output_path,
            )

        except Exception as exc:

            failed += 1

            logger.exception(
                "Failed to process %s: %s",
                file_path.name,
                exc,
            )

    logger.info(
        "Processing finished | "
        "Successful: %d | Failed: %d",
        successful,
        failed,
    )


def main() -> None:

    process_all_documents()


if __name__ == "__main__":
    main()