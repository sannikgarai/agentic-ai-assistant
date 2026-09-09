"""
backend/app/api/chat.py

Chat API routes.

Handles:
- Text chat requests
- PDF document requests
- Multimodal image requests
- PDF text extraction
- OCR for scanned PDFs
- Agent execution
- Chat service status
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
)
from pydantic import BaseModel, Field

from backend.app.agent.agent import Agent
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.security import (
    get_current_user,
    get_user_id,
)
from backend.app.documents.ocr import OCREngine
from backend.app.documents.parser import DocumentParser


# ---------------------------------------------------------------------
# Router and logger
# ---------------------------------------------------------------------

router = APIRouter()

logger = get_logger(__name__)

agent = Agent()
document_parser = DocumentParser()
ocr_engine = OCREngine()


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

MAX_CHAT_FILE_SIZE = min(
    settings.max_upload_size,
    10 * 1024 * 1024,
)

SUPPORTED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

SUPPORTED_DOCUMENT_TYPES = {
    "application/pdf",
}

SUPPORTED_FILE_TYPES = (
    SUPPORTED_IMAGE_TYPES
    | SUPPORTED_DOCUMENT_TYPES
)

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


# ---------------------------------------------------------------------
# Response model
# ---------------------------------------------------------------------

class ChatResponse(BaseModel):
    """Response returned by the chat endpoint."""

    success: bool

    message: str

    conversation_id: str | None = None

    language: str

    user_id: str

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _error_response(
    *,
    message: str,
    conversation_id: str | None,
    language: str,
    user_id: str,
    status_value: str,
    metadata: dict[str, Any] | None = None,
) -> ChatResponse:
    """
    Create a standardized unsuccessful chat response.
    """

    response_metadata: dict[str, Any] = {
        "status": status_value,
    }

    if metadata:
        response_metadata.update(metadata)

    return ChatResponse(
        success=False,
        message=message,
        conversation_id=conversation_id,
        language=language,
        user_id=user_id,
        metadata=response_metadata,
    )


def _get_file_extension(
    filename: str,
) -> str:
    """
    Return a normalized file extension.
    """

    return Path(filename).suffix.lower()


def _build_pdf_agent_message(
    user_message: str,
    filename: str,
    extracted_text: str,
    *,
    used_ocr: bool,
) -> str:
    """
    Build the Agent prompt for an uploaded PDF.

    The extracted document content is explicitly marked as
    user-provided document content so the Agent can distinguish
    it from authoritative retrieved information.
    """

    if user_message:
        instruction = user_message
    else:
        instruction = (
            "Analyze the uploaded PDF document and "
            "answer based on its contents."
        )

    extraction_method = (
        "OCR"
        if used_ocr
        else "direct PDF text extraction"
    )

    return (
        f"{instruction}\n\n"
        "USER-UPLOADED DOCUMENT CONTEXT\n"
        f"Filename: {filename}\n"
        f"Extraction method: {extraction_method}\n\n"
        "The following text was extracted from the "
        "user-provided PDF. Treat it as document content, "
        "not as independently verified government information. "
        "Do not invent missing information.\n\n"
        "----- BEGIN DOCUMENT TEXT -----\n"
        f"{extracted_text}\n"
        "----- END DOCUMENT TEXT -----"
    )


def _build_image_agent_message(
    user_message: str,
    filename: str,
) -> str:
    """
    Build the Agent prompt for an uploaded image.
    """

    if user_message:
        return user_message

    return (
        "Analyze the uploaded image and answer based "
        "on its visible contents. "
        f"The uploaded file is '{filename}'."
    )


async def _read_uploaded_file(
    file: UploadFile,
) -> bytes:
    """
    Read an uploaded file into memory.
    """

    try:
        content = await file.read()

    except Exception as exc:
        logger.exception(
            "Failed to read uploaded chat file | "
            "filename=%s",
            file.filename,
        )

        raise RuntimeError(
            "Unable to read the uploaded file."
        ) from exc

    if not content:
        raise ValueError(
            "The uploaded file is empty."
        )

    if len(content) > MAX_CHAT_FILE_SIZE:
        max_size_mb = (
            MAX_CHAT_FILE_SIZE
            / (1024 * 1024)
        )

        raise ValueError(
            f"The uploaded file is too large. "
            f"Maximum allowed size is "
            f"{max_size_mb:.0f} MB."
        )

    return content


def _write_temp_file(
    content: bytes,
    filename: str,
) -> str:
    """
    Write uploaded content to a temporary file.

    The caller is responsible for deleting the file.
    """

    suffix = _get_file_extension(filename)

    temp_file = tempfile.NamedTemporaryFile(
        mode="wb",
        suffix=suffix,
        delete=False,
    )

    try:
        temp_file.write(content)
        temp_file.flush()
        return temp_file.name

    finally:
        temp_file.close()


def _extract_pdf_text(
    *,
    content: bytes,
    filename: str,
    language: str,
) -> tuple[str, dict[str, Any]]:
    """
    Extract text from a PDF.

    First attempts normal PyMuPDF extraction.
    If one or more pages contain no extractable text,
    Tesseract OCR is run on the PDF.

    Returns:
        (text, metadata)
    """

    parsed_document = document_parser.parse_bytes(
        content=content,
        filename=filename,
    )

    direct_text = (
        parsed_document.text.strip()
    )

    page_count = (
        parsed_document.page_count
    )

    pages_requiring_ocr = list(
        parsed_document.metadata.get(
            "pages_requiring_ocr",
            [],
        )
    )

    requires_ocr = (
        parsed_document.requires_ocr
    )

    logger.info(
        "PDF parsed | filename=%s | pages=%d | "
        "direct_text_length=%d | requires_ocr=%s | "
        "ocr_pages=%s",
        filename,
        page_count,
        len(direct_text),
        requires_ocr,
        pages_requiring_ocr,
    )

    # -------------------------------------------------------------
    # PDF contains extractable text
    # -------------------------------------------------------------

    if not requires_ocr:
        return (
            direct_text,
            {
                "document_type": "pdf",
                "page_count": page_count,
                "requires_ocr": False,
                "pages_requiring_ocr": [],
                "extraction_method": "pymupdf",
                "extracted_text_length": len(
                    direct_text
                ),
            },
        )

    # -------------------------------------------------------------
    # Scanned PDF / pages requiring OCR
    # -------------------------------------------------------------

    temp_path: str | None = None

    try:
        temp_path = _write_temp_file(
            content,
            filename,
        )

        logger.info(
            "Running OCR on PDF | filename=%s | "
            "language=%s",
            filename,
            language,
        )

        ocr_result = ocr_engine.process(
            file_path=temp_path,
            language=language,
        )

        ocr_text = str(
            ocr_result.get(
                "text",
                "",
            )
        ).strip()

        # ---------------------------------------------------------
        # Combine direct text and OCR text when both exist.
        #
        # This is useful for mixed PDFs where some pages contain
        # selectable text and other pages are scanned.
        # ---------------------------------------------------------

        if direct_text and ocr_text:
            combined_text = (
                f"{direct_text}\n\n"
                f"{ocr_text}"
            )
        else:
            combined_text = (
                ocr_text
                or direct_text
            )

        return (
            combined_text.strip(),
            {
                "document_type": "pdf",
                "page_count": page_count,
                "requires_ocr": True,
                "pages_requiring_ocr": (
                    pages_requiring_ocr
                ),
                "extraction_method": (
                    "pymupdf+ocr"
                    if direct_text
                    else "ocr"
                ),
                "ocr_language": language,
                "extracted_text_length": len(
                    combined_text
                ),
                "ocr_page_count": len(
                    ocr_result.get(
                        "pages",
                        [],
                    )
                ),
            },
        )

    finally:
        if temp_path:
            try:
                os.remove(temp_path)

            except FileNotFoundError:
                pass

            except Exception:
                logger.warning(
                    "Unable to remove temporary PDF | "
                    "path=%s",
                    temp_path,
                    exc_info=True,
                )


# ---------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------

@router.post(
    "/",
    response_model=ChatResponse,
)
async def chat(
    message: str = Form(
        default="",
        max_length=10000,
    ),
    conversation_id: str | None = Form(
        default=None,
    ),
    language: str = Form(
        default="en",
        max_length=20,
    ),
    file: UploadFile | None = File(
        default=None,
    ),
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> ChatResponse:
    """
    Process a user message and/or uploaded document
    through the Agent.

    Supported upload flow:

        React frontend
            ↓
        FastAPI /api/chat/
            ↓
        ┌───────────────────────────────┐
        │ PDF                           │
        │   ↓                           │
        │ DocumentParser                │
        │   ↓                           │
        │ PyMuPDF text extraction      │
        │   ↓                           │
        │ OCR if required               │
        │   ↓                           │
        │ Extracted document text       │
        └───────────────┬───────────────┘
                        ↓
                     Agent

        ┌───────────────────────────────┐
        │ PNG / JPEG / WEBP             │
        │   ↓                           │
        │ Image bytes + MIME type       │
        │   ↓                           │
        │ Gemini multimodal             │
        └───────────────┬───────────────┘
                        ↓
                     Agent

        Agent
            ↓
        RAG + tools + Gemini
            ↓
        ChatResponse
    """

    # -----------------------------------------------------------------
    # Authentication
    # -----------------------------------------------------------------

    try:
        user_id = get_user_id(user)

    except Exception:
        logger.warning(
            "Unable to identify authenticated user."
        )

        return _error_response(
            message=(
                "Unable to identify the current user."
            ),
            conversation_id=conversation_id,
            language=language,
            user_id="",
            status_value="authentication_error",
        )

    # -----------------------------------------------------------------
    # Normalize request
    # -----------------------------------------------------------------

    clean_message = (
        message.strip()
        if message
        else ""
    )

    normalized_language = (
        language.strip().lower()
        if language
        else "en"
    )

    logger.info(
        "Chat request received | user=%s | "
        "conversation=%s | language=%s | file=%s",
        user_id,
        conversation_id,
        normalized_language,
        file.filename if file else None,
    )

    # -----------------------------------------------------------------
    # Validate request
    # -----------------------------------------------------------------

    if not clean_message and file is None:
        return _error_response(
            message=(
                "Please provide a message or "
                "upload a document."
            ),
            conversation_id=conversation_id,
            language=normalized_language,
            user_id=user_id,
            status_value="validation_error",
        )

    # -----------------------------------------------------------------
    # File variables
    # -----------------------------------------------------------------

    file_bytes: bytes | None = None
    file_mime_type: str | None = None
    file_size = 0
    filename = ""
    extension = ""

    image_bytes: bytes | None = None
    image_mime_type: str | None = None

    document_text = ""
    document_metadata: dict[str, Any] = {}

    is_image = False
    is_pdf = False

    # -----------------------------------------------------------------
    # Process uploaded file
    # -----------------------------------------------------------------

    if file is not None:

        filename = (
            file.filename
            or "uploaded_file"
        ).strip()

        file_mime_type = (
            file.content_type or ""
        ).strip().lower()

        extension = _get_file_extension(
            filename
        )

        logger.info(
            "Processing uploaded chat file | "
            "user=%s | filename=%s | content_type=%s | "
            "extension=%s",
            user_id,
            filename,
            file_mime_type,
            extension,
        )

        # -------------------------------------------------------------
        # Validate extension
        # -------------------------------------------------------------

        if extension not in SUPPORTED_EXTENSIONS:
            return _error_response(
                message=(
                    "Unsupported file type. "
                    "Please upload a PDF, PNG, JPG, "
                    "JPEG, or WEBP file."
                ),
                conversation_id=conversation_id,
                language=normalized_language,
                user_id=user_id,
                status_value="unsupported_file_type",
                metadata={
                    "file_name": filename,
                    "file_type": file_mime_type,
                    "extension": extension,
                    "supported_extensions": sorted(
                        SUPPORTED_EXTENSIONS
                    ),
                },
            )

        # -------------------------------------------------------------
        # Validate MIME type
        #
        # Some browsers may provide an empty MIME type, so extension
        # is also used to identify the file. However, when a MIME
        # type is explicitly supplied, it must match a supported type.
        # -------------------------------------------------------------

        if (
            file_mime_type
            and file_mime_type
            not in SUPPORTED_FILE_TYPES
        ):
            return _error_response(
                message=(
                    "Unsupported file format. "
                    "Please upload a PDF, PNG, JPG, "
                    "JPEG, or WEBP file."
                ),
                conversation_id=conversation_id,
                language=normalized_language,
                user_id=user_id,
                status_value="unsupported_file_type",
                metadata={
                    "file_name": filename,
                    "file_type": file_mime_type,
                    "extension": extension,
                },
            )

        # -------------------------------------------------------------
        # Determine actual processing type
        # -------------------------------------------------------------

        is_pdf = extension == ".pdf"

        is_image = extension in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
        }

        # -------------------------------------------------------------
        # Read file
        # -------------------------------------------------------------

        try:
            file_bytes = await _read_uploaded_file(
                file
            )

        except ValueError as exc:
            return _error_response(
                message=str(exc),
                conversation_id=conversation_id,
                language=normalized_language,
                user_id=user_id,
                status_value=(
                    "empty_file"
                    if "empty" in str(exc).lower()
                    else "file_too_large"
                ),
                metadata={
                    "file_name": filename,
                },
            )

        except Exception as exc:
            logger.exception(
                "Failed to read uploaded file | "
                "user=%s | filename=%s",
                user_id,
                filename,
            )

            return _error_response(
                message=(
                    "Unable to read the uploaded file."
                ),
                conversation_id=conversation_id,
                language=normalized_language,
                user_id=user_id,
                status_value="file_read_error",
                metadata={
                    "file_name": filename,
                    "error_type": type(exc).__name__,
                },
            )

        file_size = len(file_bytes)

        logger.info(
            "Chat file loaded | user=%s | filename=%s | "
            "size=%d bytes | is_pdf=%s | is_image=%s",
            user_id,
            filename,
            file_size,
            is_pdf,
            is_image,
        )

        # -------------------------------------------------------------
        # IMAGE
        # -------------------------------------------------------------

        if is_image:

            image_bytes = file_bytes

            image_mime_type = (
                file_mime_type
                or {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".webp": "image/webp",
                }.get(
                    extension,
                    "application/octet-stream",
                )
            )

            logger.info(
                "Image prepared for multimodal Agent | "
                "user=%s | filename=%s | mime=%s",
                user_id,
                filename,
                image_mime_type,
            )

        # -------------------------------------------------------------
        # PDF
        # -------------------------------------------------------------

        elif is_pdf:

            try:
                (
                    document_text,
                    document_metadata,
                ) = _extract_pdf_text(
                    content=file_bytes,
                    filename=filename,
                    language=normalized_language,
                )

            except ValueError as exc:
                logger.warning(
                    "PDF validation/parsing failed | "
                    "user=%s | filename=%s | error=%s",
                    user_id,
                    filename,
                    exc,
                )

                return _error_response(
                    message=(
                        "Unable to process the uploaded PDF. "
                        f"{exc}"
                    ),
                    conversation_id=conversation_id,
                    language=normalized_language,
                    user_id=user_id,
                    status_value="document_processing_error",
                    metadata={
                        "file_name": filename,
                        "file_type": file_mime_type,
                    },
                )

            except RuntimeError as exc:
                logger.exception(
                    "PDF OCR/processing failed | "
                    "user=%s | filename=%s",
                    user_id,
                    filename,
                )

                return _error_response(
                    message=(
                        "The PDF could not be processed. "
                        "If it is a scanned document, make sure "
                        "Tesseract OCR is installed and the required "
                        "language data is available."
                    ),
                    conversation_id=conversation_id,
                    language=normalized_language,
                    user_id=user_id,
                    status_value="ocr_processing_error",
                    metadata={
                        "file_name": filename,
                        "file_type": file_mime_type,
                        "error_type": type(exc).__name__,
                    },
                )

            except Exception as exc:
                logger.exception(
                    "Unexpected PDF processing failure | "
                    "user=%s | filename=%s",
                    user_id,
                    filename,
                )

                return _error_response(
                    message=(
                        "Unable to process the uploaded PDF "
                        "right now."
                    ),
                    conversation_id=conversation_id,
                    language=normalized_language,
                    user_id=user_id,
                    status_value="document_processing_error",
                    metadata={
                        "file_name": filename,
                        "file_type": file_mime_type,
                        "error_type": type(exc).__name__,
                    },
                )

            # ---------------------------------------------------------
            # Make sure there is usable document content.
            # ---------------------------------------------------------

            if not document_text.strip():

                return _error_response(
                    message=(
                        "The PDF was opened successfully, "
                        "but no readable text could be extracted "
                        "from it."
                    ),
                    conversation_id=conversation_id,
                    language=normalized_language,
                    user_id=user_id,
                    status_value="no_document_text",
                    metadata={
                        "file_name": filename,
                        "file_type": file_mime_type,
                        **document_metadata,
                    },
                )

            logger.info(
                "PDF text extracted | user=%s | "
                "filename=%s | text_length=%d | method=%s",
                user_id,
                filename,
                len(document_text),
                document_metadata.get(
                    "extraction_method"
                ),
            )

    # -----------------------------------------------------------------
    # Build Agent message
    # -----------------------------------------------------------------

    agent_message = clean_message

    if is_pdf:
        agent_message = _build_pdf_agent_message(
            user_message=clean_message,
            filename=filename,
            extracted_text=document_text,
            used_ocr=bool(
                document_metadata.get(
                    "requires_ocr",
                    False,
                )
            ),
        )

    elif is_image:
        agent_message = _build_image_agent_message(
            user_message=clean_message,
            filename=filename,
        )

    # -----------------------------------------------------------------
    # Run Agent
    # -----------------------------------------------------------------

    try:

        logger.info(
            "Calling Agent | user=%s | conversation=%s | "
            "has_image=%s | has_pdf=%s | message_length=%d",
            user_id,
            conversation_id,
            bool(image_bytes),
            is_pdf,
            len(agent_message),
        )

        result = await agent.run(
            user_id=user_id,
            message=agent_message,
            conversation_id=conversation_id,
            language=normalized_language,
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
        )

        logger.info(
            "Agent response received | user=%s | "
            "success=%s | status=%s",
            user_id,
            result.success,
            result.status,
        )

        # -----------------------------------------------------------------
        # Build response metadata
        # -----------------------------------------------------------------

        response_metadata: dict[str, Any] = {
            "status": result.status,
            "has_image": bool(image_bytes),
            "has_document": file is not None,
            "document_type": (
                "pdf"
                if is_pdf
                else "image"
                if is_image
                else None
            ),
        }

        if file is not None:
            response_metadata.update(
                {
                    "file_name": filename,
                    "file_type": file_mime_type,
                    "file_extension": extension,
                    "file_size": file_size,
                }
            )

        # -------------------------------------------------------------
        # PDF metadata
        # -------------------------------------------------------------

        if is_pdf:
            response_metadata.update(
                document_metadata
            )

        # -------------------------------------------------------------
        # Agent plan
        # -------------------------------------------------------------

        if result.plan is not None:
            response_metadata["plan"] = (
                result.plan
            )

        # -------------------------------------------------------------
        # Agent metadata
        # -------------------------------------------------------------

        if result.metadata:
            response_metadata.update(
                result.metadata
            )

        # -----------------------------------------------------------------
        # Build final response
        # -----------------------------------------------------------------

        conversation_result_id = (
            result.state.conversation_id
            if result.state is not None
            else conversation_id
        )

        result_language = (
            result.state.language
            if result.state is not None
            else normalized_language
        )

        return ChatResponse(
            success=result.success,
            message=result.response,
            conversation_id=conversation_result_id,
            language=result_language,
            user_id=user_id,
            metadata=response_metadata,
        )

    except Exception as exc:

        logger.exception(
            "Chat/Agent processing failed | "
            "user=%s | conversation=%s | error_type=%s",
            user_id,
            conversation_id,
            type(exc).__name__,
        )

        return _error_response(
            message=(
                "Unable to process your request right now. "
                "Please try again."
            ),
            conversation_id=conversation_id,
            language=normalized_language,
            user_id=user_id,
            status_value="error",
            metadata={
                "error_type": type(exc).__name__,
                "has_image": bool(image_bytes),
                "has_document": file is not None,
                "file_name": (
                    filename
                    if file is not None
                    else None
                ),
            },
        )


# ---------------------------------------------------------------------
# Chat service status
# ---------------------------------------------------------------------

@router.get(
    "/status",
)
async def chat_status(
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Return the current chat service status.
    """

    user_id = get_user_id(user)

    return {
        "success": True,
        "service": "chat",
        "status": "available",
        "user_id": user_id,
        "supported_files": [
            "application/pdf",
            "image/png",
            "image/jpeg",
            "image/webp",
        ],
        "max_file_size": MAX_CHAT_FILE_SIZE,
    }