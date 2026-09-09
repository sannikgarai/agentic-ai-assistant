"""
Verification API routes.

Handles document/data verification requests and
verification status retrieval.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.logging import get_logger
from backend.app.core.security import (
    get_current_user,
    get_user_id,
)
from backend.app.database.repositories.verification import (
    VerificationRepository,
)


# ---------------------------------------------------------------------
# Router and logger
# ---------------------------------------------------------------------

router = APIRouter()

logger = get_logger(__name__)

verification_repository = VerificationRepository()


# ---------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------

class VerificationRequest(BaseModel):
    """
    Request for document/data verification.
    """

    document_id: str = Field(
        ...,
        min_length=1,
    )

    reference_document_id: str | None = Field(
        default=None,
    )

    fields: dict[str, Any] = Field(
        default_factory=dict,
    )


# ---------------------------------------------------------------------
# Verification endpoint
# ---------------------------------------------------------------------

@router.post("/check")
async def verify_document(
    request: VerificationRequest,
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Create a verification request.

    The verification engine can subsequently process
    the stored verification record.
    """

    user_id = get_user_id(user)

    logger.info(
        "Verification request received | user=%s | "
        "document=%s | reference=%s",
        user_id,
        request.document_id,
        request.reference_document_id,
    )

    # -----------------------------------------------------------------
    # Basic validation
    # -----------------------------------------------------------------

    if (
        request.reference_document_id
        and request.document_id
        == request.reference_document_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Document and reference document "
                "must be different."
            ),
        )

    # -----------------------------------------------------------------
    # Build initial verification details
    # -----------------------------------------------------------------

    details: dict[str, Any] = {
        "fields": request.fields,
        "reference_document_id": (
            request.reference_document_id
        ),
        "matched_fields": [],
        "mismatched_fields": [],
        "missing_fields": [],
        "verification_method": "document",
    }

    # -----------------------------------------------------------------
    # Create verification record
    # -----------------------------------------------------------------

    try:
        verification = (
            verification_repository.create(
                user_id=user_id,
                status="pending",
                verification_type="document",
                document_id=request.document_id,
                details=details,
            )
        )

    except Exception as exc:
        logger.exception(
            "Failed to create verification record | "
            "user=%s | document=%s",
            user_id,
            request.document_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create the verification request."
            ),
        ) from exc

    verification_id = verification.get("id")

    logger.info(
        "Verification record created | user=%s | "
        "verification=%s",
        user_id,
        verification_id,
    )

    return {
        "success": True,
        "status": verification.get(
            "status",
            "pending",
        ),
        "verification_id": verification_id,
        "document_id": request.document_id,
        "reference_document_id": (
            request.reference_document_id
        ),
        "user_id": user_id,
        "result": {
            "matched_fields": [],
            "mismatched_fields": [],
            "missing_fields": [],
        },
        "message": (
            "Verification request created successfully."
        ),
    }


# ---------------------------------------------------------------------
# Verification status
# ---------------------------------------------------------------------

@router.get("/status/{verification_id}")
async def verification_status(
    verification_id: str,
    user: dict[str, Any] = Depends(
        get_current_user,
    ),
) -> dict[str, Any]:
    """
    Get the status and result of a verification request.
    """

    user_id = get_user_id(user)

    verification_id = verification_id.strip()

    if not verification_id:
        raise HTTPException(
            status_code=400,
            detail="Verification ID is required.",
        )

    logger.info(
        "Verification status requested | user=%s | "
        "verification=%s",
        user_id,
        verification_id,
    )

    # -----------------------------------------------------------------
    # Fetch verification record
    # -----------------------------------------------------------------

    try:
        verification = (
            verification_repository.get(
                verification_id=verification_id,
            )
        )

    except Exception as exc:
        logger.exception(
            "Failed to fetch verification | "
            "user=%s | verification=%s",
            user_id,
            verification_id,
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to retrieve the verification record."
            ),
        ) from exc

    # -----------------------------------------------------------------
    # Verify existence
    # -----------------------------------------------------------------

    if verification is None:
        raise HTTPException(
            status_code=404,
            detail="Verification record not found.",
        )

    # -----------------------------------------------------------------
    # Ownership check
    # -----------------------------------------------------------------

    verification_user_id = verification.get(
        "user_id"
    )

    if (
        not verification_user_id
        or str(verification_user_id) != user_id
    ):
        logger.warning(
            "Unauthorized verification access attempt | "
            "user=%s | verification=%s",
            user_id,
            verification_id,
        )

        raise HTTPException(
            status_code=403,
            detail=(
                "You do not have access to this "
                "verification record."
            ),
        )

    # -----------------------------------------------------------------
    # Extract details safely
    # -----------------------------------------------------------------

    details = verification.get(
        "details"
    )

    if not isinstance(details, dict):
        details = {}

    result = {
        "matched_fields": details.get(
            "matched_fields",
            [],
        ),
        "mismatched_fields": details.get(
            "mismatched_fields",
            [],
        ),
        "missing_fields": details.get(
            "missing_fields",
            [],
        ),
    }

    return {
        "success": True,
        "verification_id": verification_id,
        "status": verification.get(
            "status",
            "pending",
        ),
        "verification": verification,
        "result": result,
        "user_id": user_id,
    }