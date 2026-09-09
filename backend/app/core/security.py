"""
backend/app/core/security.py

Security utilities for the Agentic AI Assistant backend.

This module provides:
- Bearer token extraction
- Supabase JWT/access-token validation
- FastAPI authentication dependencies
- Optional authentication
- User ID helpers
"""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from backend.app.core.config import settings


# ---------------------------------------------------------------------
# HTTP Bearer Authentication
# ---------------------------------------------------------------------

bearer_scheme = HTTPBearer(
    auto_error=False,
)


# ---------------------------------------------------------------------
# Authentication Exceptions
# ---------------------------------------------------------------------

def authentication_error(
    detail: str = "Authentication required.",
) -> HTTPException:
    """
    Create a standard HTTP 401 authentication error.
    """

    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


# ---------------------------------------------------------------------
# Supabase User Validation
# ---------------------------------------------------------------------

async def get_supabase_user(
    access_token: str,
) -> dict[str, Any]:
    """
    Validate a Supabase access token and return
    the authenticated user's information.

    Supabase's /auth/v1/user endpoint validates the
    supplied access token and returns the corresponding
    authenticated user.
    """

    if not settings.supabase_url:
        raise authentication_error(
            "Supabase URL is not configured.",
        )

    if not settings.supabase_anon_key:
        raise authentication_error(
            "Supabase anonymous key is not configured.",
        )

    if not isinstance(access_token, str):
        raise authentication_error(
            "Invalid authentication token.",
        )

    access_token = access_token.strip()

    if not access_token:
        raise authentication_error(
            "Authentication token is missing.",
        )

    url = (
        f"{settings.supabase_url.rstrip('/')}"
        "/auth/v1/user"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "apikey": settings.supabase_anon_key,
        "Accept": "application/json",
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=5.0,
                read=10.0,
                write=10.0,
                pool=5.0,
            ),
        ) as client:

            response = await client.get(
                url,
                headers=headers,
            )

    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service timed out.",
        ) from exc

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is unavailable.",
        ) from exc

    # Supabase successfully authenticated the token.
    if response.status_code == status.HTTP_200_OK:
        try:
            user = response.json()

        except ValueError as exc:
            raise authentication_error(
                "Invalid authentication response.",
            ) from exc

        if (
            not isinstance(user, dict)
            or not user.get("id")
        ):
            raise authentication_error(
                "Invalid authenticated user.",
            )

        return user

    # Authentication failed.
    if response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ):
        raise authentication_error(
            "Invalid or expired authentication token.",
        )

    # Supabase returned an unexpected server-side error.
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Authentication service returned an unexpected response.",
    )


# ---------------------------------------------------------------------
# Required Authentication Dependency
# ---------------------------------------------------------------------

async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
) -> dict[str, Any]:
    """
    FastAPI dependency that returns the currently
    authenticated Supabase user.

    Example:

        @router.get("/profile")
        async def profile(
            user: dict[str, Any] = Depends(get_current_user),
        ):
            return user
    """

    if credentials is None:
        raise authentication_error()

    if credentials.scheme.lower() != "bearer":
        raise authentication_error(
            "Invalid authentication scheme.",
        )

    token = credentials.credentials

    if not isinstance(token, str):
        raise authentication_error(
            "Invalid authentication token.",
        )

    token = token.strip()

    if not token:
        raise authentication_error(
            "Authentication token is missing.",
        )

    return await get_supabase_user(token)


# ---------------------------------------------------------------------
# Optional Authentication Dependency
# ---------------------------------------------------------------------

async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
) -> dict[str, Any] | None:
    """
    Return the authenticated Supabase user if a valid
    token is supplied.

    Returns None when:
    - No Authorization header is supplied.
    - The authentication scheme is not Bearer.
    - The token is empty.
    - The token is invalid or expired.

    Useful for endpoints that support both authenticated
    and unauthenticated users.
    """

    if credentials is None:
        return None

    if credentials.scheme.lower() != "bearer":
        return None

    token = credentials.credentials

    if not isinstance(token, str):
        return None

    token = token.strip()

    if not token:
        return None

    try:
        return await get_supabase_user(token)

    except HTTPException:
        return None


# ---------------------------------------------------------------------
# User ID Helper
# ---------------------------------------------------------------------

def get_user_id(
    user: dict[str, Any],
) -> str:
    """
    Extract the Supabase user ID from an authenticated
    user object.

    Raises:
        HTTPException: If the user ID is missing.
    """

    if not isinstance(user, dict):
        raise authentication_error(
            "Invalid authenticated user.",
        )

    user_id = user.get("id")

    if not user_id:
        raise authentication_error(
            "Authenticated user ID is missing.",
        )

    return str(user_id)


# ---------------------------------------------------------------------
# User Email Helper
# ---------------------------------------------------------------------

def get_user_email(
    user: dict[str, Any],
) -> str | None:
    """
    Extract the authenticated user's email address.

    Returns None if an email is not available.
    """

    if not isinstance(user, dict):
        return None

    email = user.get("email")

    if not email:
        return None

    return str(email)