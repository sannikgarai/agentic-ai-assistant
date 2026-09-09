"""
File handling utilities.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


ALLOWED_FILE_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def get_file_extension(
    filename: str,
) -> str:
    """Return a lowercase file extension."""

    if not filename:
        return ""

    return Path(filename).suffix.lower()


def is_allowed_file(
    filename: str,
) -> bool:
    """Check whether a file extension is supported."""

    extension = get_file_extension(
        filename
    )

    return extension in ALLOWED_FILE_EXTENSIONS


def sanitize_filename(
    filename: str,
) -> str:
    """
    Remove unsafe characters from a filename.

    The returned filename is safe to use as a local
    filesystem filename.
    """

    if not filename:
        return "file"

    name = Path(filename).name

    name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        name,
    )

    name = re.sub(
        r"_+",
        "_",
        name,
    )

    if not name:
        return "file"

    return name


def get_file_size(
    file_path: str | Path,
) -> int:
    """Return file size in bytes."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File not found: {path}"
        )

    return path.stat().st_size


def validate_file_size(
    file_path: str | Path,
    max_size_mb: float | None = None,
) -> bool:
    """
    Check whether a file is within the configured
    maximum size.
    """

    size = get_file_size(file_path)

    if max_size_mb is None:
        max_size_mb = (
            settings.max_upload_size_mb
        )

    max_size_bytes = int(
        max_size_mb * 1024 * 1024
    )

    return size <= max_size_bytes


def generate_unique_filename(
    filename: str,
) -> str:
    """
    Generate a unique filename while preserving
    the original extension.
    """

    safe_name = sanitize_filename(
        filename
    )

    extension = get_file_extension(
        safe_name
    )

    return (
        f"{uuid4().hex}{extension}"
    )


async def save_upload_file(
    upload_file: UploadFile,
    destination_dir: str | Path | None = None,
) -> tuple[Path, int]:
    """
    Save an uploaded file safely.

    Returns:
        (saved_file_path, file_size_bytes)
    """

    if not upload_file.filename:
        raise ValueError(
            "Uploaded file has no filename."
        )

    if not is_allowed_file(
        upload_file.filename
    ):
        extension = get_file_extension(
            upload_file.filename
        )

        raise ValueError(
            f"Unsupported file type: {extension}. "
            f"Allowed types: "
            f"{', '.join(sorted(ALLOWED_FILE_EXTENSIONS))}"
        )

    if destination_dir is None:
        destination_dir = (
            settings.uploaded_document_dir
        )

    destination = Path(
        destination_dir
    )

    destination.mkdir(
        parents=True,
        exist_ok=True,
    )

    unique_filename = (
        generate_unique_filename(
            upload_file.filename
        )
    )

    file_path = (
        destination / unique_filename
    )

    max_size_bytes = int(
        settings.max_upload_size_mb
        * 1024
        * 1024
    )

    total_size = 0

    try:
        with file_path.open(
            "wb"
        ) as output_file:

            while True:
                chunk = await upload_file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size_bytes:
                    output_file.close()

                    if file_path.exists():
                        file_path.unlink()

                    raise ValueError(
                        "Uploaded file exceeds "
                        f"the maximum size of "
                        f"{settings.max_upload_size_mb} MB."
                    )

                output_file.write(chunk)

    finally:
        await upload_file.close()

    return file_path, total_size


def delete_file(
    file_path: str | Path,
) -> bool:
    """Delete a file if it exists."""

    path = Path(file_path)

    if not path.exists():
        return False

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {path}"
        )

    path.unlink()

    return True