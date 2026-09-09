"""
Document models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class DocumentField(BaseModel):
    """A field extracted from a document."""

    name: str

    value: str | None = None

    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    source: str | None = None

    verified: bool = False


class Document(BaseModel):
    """Document database record."""

    model_config = ConfigDict(
        from_attributes=True
    )

    id: str

    user_id: str

    file_name: str

    file_path: str

    document_type: str = "unknown"

    mime_type: str | None = None

    file_size: int | None = Field(
        default=None,
        ge=0,
    )

    fields: list[DocumentField] = Field(
        default_factory=list
    )

    extracted_text: str | None = None

    processing_status: str = "pending"

    metadata: dict[str, Any] = Field(
        default_factory=dict
    )

    created_at: datetime | None = None

    updated_at: datetime | None = None


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    document_id: str

    file_name: str

    document_type: str

    processing_status: str

    extracted_fields: list[
        DocumentField
    ] = Field(
        default_factory=list
    )

    message: str = "Document uploaded successfully."


class DocumentProcessingRequest(BaseModel):
    """Options for processing a document."""

    document_id: str

    use_ocr: bool = True

    language: str = "en"

    extract_fields: bool = True