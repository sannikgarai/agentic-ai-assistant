"""
Document API routes.

Handles:
- Document upload
- Supabase Storage persistence
- Supabase database metadata persistence
- Document retrieval
- Document listing
- Document deletion
- Document extraction
- OCR
- Document classification
- Structured information extraction
- Document analysis
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from backend.app.core.config import settings
from backend.app.core.security import (
    get_current_user,
    get_user_id,
)

from backend.app.database.repositories.documents import (
    DocumentRepository,
)

from backend.app.documents.parser import (
    DocumentParser,
)

from backend.app.documents.classifier import (
    DocumentClassifier,
)

from backend.app.documents.extractor import (
    DocumentExtractor,
)

from backend.app.documents.ocr import (
    OCREngine,
)


router = APIRouter()


# ==========================================================
# CONSTANTS
# ==========================================================

STORAGE_BUCKET = "documents"

ALLOWED_DOCUMENT_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}

MAX_DOCUMENT_SIZE = 20 * 1024 * 1024  # 20 MB


# ==========================================================
# SERVICES
# ==========================================================

document_repository = DocumentRepository()

document_parser = DocumentParser()

document_classifier = DocumentClassifier()

document_extractor = DocumentExtractor()

ocr_engine = OCREngine()


# ==========================================================
# HELPERS
# ==========================================================


def _get_extension(
    filename: str,
) -> str:
    """
    Return a normalized file extension.
    """

    if "." not in filename:
        return ""

    return (
        "."
        + filename.rsplit(
            ".",
            1,
        )[1].lower()
    )


def _get_document_for_user(
    document_id: str,
    user_id: str,
) -> dict[str, Any] | None:
    """
    Get a document only when it belongs to
    the authenticated user.
    """

    document = document_repository.get(
        document_id
    )

    if not document:
        return None

    if str(
        document.get("user_id")
    ) != str(user_id):
        return None

    return document


def _storage_path(
    user_id: str,
    document_id: str,
    extension: str,
) -> str:
    """
    Create a safe Supabase Storage object path.

    Example:

        user-id/document-id.pdf
    """

    return (
        f"{user_id}/"
        f"{document_id}"
        f"{extension}"
    )


def _download_from_storage(
    storage_path: str,
    local_path: Path,
) -> Path:
    """
    Download a document from Supabase Storage
    into the temporary directory.
    """

    database = document_repository.database

    file_bytes = (
        database.client
        .storage
        .from_(STORAGE_BUCKET)
        .download(storage_path)
    )

    if not file_bytes:
        raise RuntimeError(
            "The document could not be downloaded "
            "from Supabase Storage."
        )

    local_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    local_path.write_bytes(
        file_bytes
    )

    return local_path


def _delete_from_storage(
    storage_path: str,
) -> None:
    """
    Delete an object from Supabase Storage.
    """

    database = document_repository.database

    (
        database.client
        .storage
        .from_(STORAGE_BUCKET)
        .remove(
            [storage_path]
        )
    )


def _process_document(
    document: dict[str, Any],
    file_path: Path,
) -> dict[str, Any]:
    """
    Parse, OCR, classify and extract information
    from a local temporary copy of the document.
    """

    filename = document.get(
        "file_name",
        "document",
    )

    # ======================================================
    # PARSE
    # ======================================================

    parsed_document = document_parser.parse(
        file_path
    )

    text = str(
        getattr(
            parsed_document,
            "text",
            "",
        )
        or ""
    )

    # ======================================================
    # OCR
    # ======================================================

    ocr_result = None

    parsed_metadata = getattr(
        parsed_document,
        "metadata",
        {},
    )

    if not isinstance(
        parsed_metadata,
        dict,
    ):
        parsed_metadata = {}

    requires_ocr = bool(
        parsed_metadata.get(
            "requires_ocr",
            False,
        )
    )

    if (
        requires_ocr
        or not text.strip()
    ):
        ocr_result = ocr_engine.process(
            file_path=file_path,
            language="eng",
        )

        ocr_text = str(
            ocr_result.get(
                "text",
                "",
            )
        ).strip()

        if ocr_text:
            text = ocr_text

    # ======================================================
    # CLASSIFICATION
    # ======================================================

    classification = (
        document_classifier.classify(
            text=text,
            filename=filename,
        )
    )

    # ======================================================
    # STRUCTURED EXTRACTION
    # ======================================================

    extraction = (
        document_extractor.extract(
            text=text,
            document_type=(
                classification.document_type
            ),
        )
    )

    return {
        "parsed_document": (
            parsed_document.to_dict()
        ),
        "ocr": ocr_result,
        "classification": (
            classification.to_dict()
        ),
        "extraction": (
            extraction.to_dict()
        ),
        "text": text,
    }


def _safe_json(
    value: Any,
) -> Any:
    """
    Convert an object into JSON-compatible data.
    """

    try:
        json.dumps(value)
        return value
    except (
        TypeError,
        ValueError,
    ):
        return str(value)


def _cleanup_temp_file(
    file_path: Path,
) -> None:
    """
    Remove temporary processing file.
    """

    try:
        if file_path.exists():
            file_path.unlink()
    except OSError:
        pass


def _process_and_save_document(
    document: dict[str, Any],
    document_id: str,
    analysis: bool = False,
) -> dict[str, Any]:
    """
    Common document processing pipeline.

    Pipeline:

        Supabase Storage
              ↓
        Temporary local file
              ↓
        Parser
              ↓
        OCR when required
              ↓
        Classification
              ↓
        Structured extraction
              ↓
        Supabase database
              ↓
        completed
    """

    storage_path = document.get(
        "file_path"
    )

    if not storage_path:
        raise RuntimeError(
            "Document storage path is missing."
        )

    suffix = Path(
        storage_path
    ).suffix.lower()

    temp_path = (
        settings.temp_dir
        / f"{document_id}{suffix}"
    )

    try:
        # --------------------------------------------------
        # Mark processing
        # --------------------------------------------------

        document_repository.update(
            document_id,
            {
                "processing_status": "processing",
            },
        )

        # --------------------------------------------------
        # Download
        # --------------------------------------------------

        _download_from_storage(
            storage_path,
            temp_path,
        )

        # --------------------------------------------------
        # Process
        # --------------------------------------------------

        result = _process_document(
            document,
            temp_path,
        )

        classification = result.get(
            "classification",
            {},
        )

        extraction = result.get(
            "extraction",
            {},
        )

        text = str(
            result.get(
                "text",
                "",
            )
            or ""
        )

        if isinstance(
            classification,
            dict,
        ):
            document_type = classification.get(
                "document_type",
                "unknown",
            )
        else:
            document_type = "unknown"

        # --------------------------------------------------
        # Existing metadata
        # --------------------------------------------------

        existing_metadata = (
            document.get(
                "metadata"
            )
            or {}
        )

        if not isinstance(
            existing_metadata,
            dict,
        ):
            existing_metadata = {}

        metadata = dict(
            existing_metadata
        )

        # --------------------------------------------------
        # Save processing information
        # --------------------------------------------------

        metadata.update(
            {
                "classification": _safe_json(
                    classification
                ),
                "extraction": _safe_json(
                    extraction
                ),
                "ocr": _safe_json(
                    result.get(
                        "ocr"
                    )
                ),
                "processing": {
                    "parser": True,
                    "ocr": (
                        result.get(
                            "ocr"
                        )
                        is not None
                    ),
                    "classifier": True,
                    "extractor": True,
                },
            }
        )

        # --------------------------------------------------
        # Save complete analysis
        # --------------------------------------------------

        if analysis:
            metadata["analysis"] = _safe_json(
                result
            )

        # --------------------------------------------------
        # Persist
        # --------------------------------------------------

        updated_document = (
            document_repository.update(
                document_id,
                {
                    "document_type": (
                        document_type
                    ),
                    "extracted_text": text,
                    "metadata": metadata,
                    "processing_status": (
                        "completed"
                    ),
                },
            )
        )

        return {
            "success": True,
            "document_id": document_id,
            "processing_status": "completed",
            "document": updated_document,
            "classification": classification,
            "extraction": extraction,
            "ocr": result.get(
                "ocr"
            ),
            "text": text,
        }

    except Exception as exc:
        # --------------------------------------------------
        # Mark failed
        # --------------------------------------------------

        try:
            existing_metadata = (
                document.get(
                    "metadata"
                )
                or {}
            )

            if not isinstance(
                existing_metadata,
                dict,
            ):
                existing_metadata = {}

            failure_metadata = dict(
                existing_metadata
            )

            failure_metadata[
                "processing_error"
            ] = str(exc)

            document_repository.update(
                document_id,
                {
                    "processing_status": "failed",
                    "metadata": failure_metadata,
                },
            )

        except Exception:
            pass

        raise

    finally:
        _cleanup_temp_file(
            temp_path
        )


# ==========================================================
# DOCUMENT SERVICE STATUS
# ==========================================================


@router.get("/service/status")
async def document_service_status(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return document service status.
    """

    return {
        "success": True,
        "service": "documents",
        "status": "available",
        "storage": STORAGE_BUCKET,
        "user_id": get_user_id(user),
    }


# ==========================================================
# UPLOAD DOCUMENT
# ==========================================================


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Upload a document and automatically process it.

    Pipeline:

        Upload
          ↓
        Supabase Storage
          ↓
        Database
          ↓
        Processing
          ↓
        Parser
          ↓
        OCR
          ↓
        Classification
          ↓
        Extraction
          ↓
        completed
    """

    user_id = get_user_id(user)

    # ======================================================
    # VALIDATE FILENAME
    # ======================================================

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    filename = Path(
        file.filename
    ).name

    extension = _get_extension(
        filename
    )

    # ======================================================
    # VALIDATE EXTENSION
    # ======================================================

    if extension not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported file type: "
                f"{extension or 'unknown'}"
            ),
        )

    # ======================================================
    # READ FILE
    # ======================================================

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    file_size = len(
        file_bytes
    )

    # ======================================================
    # VALIDATE SIZE
    # ======================================================

    if file_size > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "File is too large. "
                "Maximum allowed size is 20 MB."
            ),
        )

    # ======================================================
    # CREATE DOCUMENT ID
    # ======================================================

    document_id = str(
        uuid4()
    )

    # ======================================================
    # STORAGE PATH
    # ======================================================

    storage_path = _storage_path(
        user_id=user_id,
        document_id=document_id,
        extension=extension,
    )

    database = document_repository.database

    # ======================================================
    # UPLOAD TO SUPABASE STORAGE
    # ======================================================

    try:
        (
            database.client
            .storage
            .from_(STORAGE_BUCKET)
            .upload(
                storage_path,
                file_bytes,
                {
                    "content-type": (
                        file.content_type
                        or "application/octet-stream"
                    ),
                    "upsert": False,
                },
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Failed to upload document "
                "to Supabase Storage."
            ),
        ) from exc

    # ======================================================
    # CREATE DATABASE RECORD
    # ======================================================

    try:
        document_response = (
            database
            .table("documents")
            .insert(
                {
                    "id": document_id,
                    "user_id": user_id,
                    "file_name": filename,
                    "file_path": storage_path,
                    "mime_type": (
                        file.content_type
                        or "application/octet-stream"
                    ),
                    "file_size": file_size,
                    "document_type": "unknown",
                    "processing_status": "pending",
                    "metadata": {
                        "original_filename": filename,
                        "extension": extension,
                        "storage_bucket": (
                            STORAGE_BUCKET
                        ),
                    },
                }
            )
            .execute()
        )

        if not document_response.data:
            raise RuntimeError(
                "Document database record "
                "was not created."
            )

        document_record = (
            document_response.data[0]
        )

    except Exception as exc:
        # --------------------------------------------------
        # Roll back Storage
        # --------------------------------------------------

        try:
            _delete_from_storage(
                storage_path
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document was uploaded to Storage "
                "but its database record could not "
                "be created."
            ),
        ) from exc

    # ======================================================
    # AUTOMATIC PROCESSING
    # ======================================================

    try:
        processing_result = (
            _process_and_save_document(
                document=document_record,
                document_id=document_id,
                analysis=True,
            )
        )

        # --------------------------------------------------
        # Return completed document
        # --------------------------------------------------

        return {
            "success": True,
            "message": (
                "Document uploaded and "
                "analyzed successfully."
            ),
            "document": (
                processing_result.get(
                    "document"
                )
                or {
                    **document_record,
                    "processing_status": (
                        "completed"
                    ),
                }
            ),
            "processing_status": "completed",
            "classification": (
                processing_result.get(
                    "classification"
                )
            ),
            "extraction": (
                processing_result.get(
                    "extraction"
                )
            ),
            "ocr": (
                processing_result.get(
                    "ocr"
                )
            ),
        }

    except Exception as exc:
        # --------------------------------------------------
        # IMPORTANT:
        # The file was uploaded successfully,
        # but processing failed.
        # --------------------------------------------------

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document uploaded successfully, "
                "but document processing failed."
            ),
        ) from exc


# ==========================================================
# LIST DOCUMENTS
# ==========================================================


@router.get("/")
async def list_documents(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return all documents belonging to
    the authenticated user.
    """

    user_id = get_user_id(user)

    try:
        documents = (
            document_repository
            .list_for_user(
                user_id=user_id
            )
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to retrieve documents."
            ),
        ) from exc

    return {
        "success": True,
        "documents": documents,
        "user_id": user_id,
    }


# ==========================================================
# GET DOCUMENT
# ==========================================================


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return one document belonging to
    the authenticated user.
    """

    user_id = get_user_id(user)

    document = _get_document_for_user(
        document_id,
        user_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return {
        "success": True,
        "document": document,
    }


# ==========================================================
# EXTRACT DOCUMENT
# ==========================================================


@router.post("/{document_id}/extract")
async def extract_document(
    document_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Extract information from an existing document.
    """

    user_id = get_user_id(user)

    document = _get_document_for_user(
        document_id,
        user_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    try:
        result = _process_and_save_document(
            document=document,
            document_id=document_id,
            analysis=False,
        )

        return {
            "success": True,
            "message": (
                "Document extracted successfully."
            ),
            "document_id": document_id,
            "processing_status": "completed",
            "classification": (
                result.get(
                    "classification"
                )
            ),
            "extraction": (
                result.get(
                    "extraction"
                )
            ),
            "ocr": (
                result.get(
                    "ocr"
                )
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document extraction failed."
            ),
        ) from exc


# ==========================================================
# ANALYZE DOCUMENT
# ==========================================================


@router.post("/{document_id}/analyze")
async def analyze_document(
    document_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Fully analyze an existing document.
    """

    user_id = get_user_id(user)

    document = _get_document_for_user(
        document_id,
        user_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    try:
        result = _process_and_save_document(
            document=document,
            document_id=document_id,
            analysis=True,
        )

        return {
            "success": True,
            "message": (
                "Document analyzed successfully."
            ),
            "document_id": document_id,
            "processing_status": "completed",
            "classification": (
                result.get(
                    "classification"
                )
            ),
            "extraction": (
                result.get(
                    "extraction"
                )
            ),
            "ocr": (
                result.get(
                    "ocr"
                )
            ),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document analysis failed."
            ),
        ) from exc


# ==========================================================
# DOCUMENT STATUS
# ==========================================================


@router.get("/{document_id}/status")
async def get_document_status(
    document_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return the persistent processing status
    of a document.
    """

    user_id = get_user_id(user)

    document = _get_document_for_user(
        document_id,
        user_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return {
        "success": True,
        "document_id": document_id,
        "status": document.get(
            "processing_status",
            "pending",
        ),
    }


# ==========================================================
# DELETE DOCUMENT
# ==========================================================


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Delete a document from both:

        1. Supabase Storage
        2. Supabase documents table
    """

    user_id = get_user_id(user)

    document = _get_document_for_user(
        document_id,
        user_id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    storage_path = document.get(
        "file_path"
    )

    # ======================================================
    # DELETE STORAGE OBJECT
    # ======================================================

    if storage_path:
        try:
            _delete_from_storage(
                storage_path
            )

        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Unable to delete the document "
                    "from Supabase Storage."
                ),
            ) from exc

    # ======================================================
    # DELETE DATABASE RECORD
    # ======================================================

    try:
        deleted = (
            document_repository.delete(
                document_id
            )
        )

        if not deleted:
            raise RuntimeError(
                "Document database record "
                "could not be deleted."
            )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Document file was removed from "
                "Storage, but its database record "
                "could not be deleted."
            ),
        ) from exc

    return {
        "success": True,
        "message": (
            "Document deleted successfully."
        ),
        "document_id": document_id,
    }