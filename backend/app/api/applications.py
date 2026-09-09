
"""
Application API routes.

Handles government/service application workflows.

The actual browser automation and form submission
will be connected through the automation package later.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.app.core.security import get_current_user
from backend.app.database.repositories.applications import (
    ApplicationRepository,
)


router = APIRouter()

application_repository = ApplicationRepository()


# --------------------------------------------------
# Request Models
# --------------------------------------------------

class ApplicationRequest(BaseModel):
    """
    Request to create an application.
    """

    scheme_name: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    application_data: dict[str, Any] = Field(
        default_factory=dict
    )

    document_ids: list[str] = Field(
        default_factory=list
    )


# --------------------------------------------------
# Create Application
# --------------------------------------------------

@router.post("/")
async def create_application(
    request: ApplicationRequest,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Create a new application workflow.

    The application is stored in Supabase.
    Browser automation and final submission are
    handled later by the automation workflow.
    """

    user_id = str(user["id"])

    application = application_repository.create(
        user_id=user_id,
        scheme_name=request.scheme_name,
        status="draft",
        metadata={
            "application_data": request.application_data,
            "document_ids": request.document_ids,
        },
    )

    return {
        "success": True,
        "status": application.get(
            "status",
            "draft",
        ),
        "application_id": application.get("id"),
        "scheme_name": application.get(
            "scheme_name",
            request.scheme_name,
        ),
        "application_data": request.application_data,
        "document_ids": request.document_ids,
        "user_id": user_id,
        "message": (
            "Application created successfully. "
            "The agent workflow can now process it."
        ),
    }


# --------------------------------------------------
# List Applications
# --------------------------------------------------

@router.get("/")
async def list_applications(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return the user's applications.
    """

    user_id = str(user["id"])

    applications = (
        application_repository.list_for_user(
            user_id=user_id,
            limit=100,
        )
    )

    return {
        "success": True,
        "applications": applications,
        "user_id": user_id,
    }


# --------------------------------------------------
# Application Status
# --------------------------------------------------

@router.get("/{application_id}")
async def application_status(
    application_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return the status of an application.
    """

    user_id = str(user["id"])

    application = application_repository.get(
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    if str(application.get("user_id")) != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this application.",
        )

    return {
        "success": True,
        "application_id": application_id,
        "status": application.get(
            "status",
            "draft",
        ),
        "application": application,
        "user_id": user_id,
    }
