"""
Common validation utilities.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse


EMAIL_PATTERN = re.compile(
    r"^[A-Za-z0-9._%+-]+"
    r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)

INDIAN_PHONE_PATTERN = re.compile(
    r"^(?:\+91[\s-]?)?[6-9]\d{9}$"
)

PAN_PATTERN = re.compile(
    r"^[A-Z]{5}[0-9]{4}[A-Z]$"
)

AADHAAR_PATTERN = re.compile(
    r"^\d{4}\s?\d{4}\s?\d{4}$"
)


def validate_required(
    value: Any,
    field_name: str = "Field",
) -> str:
    """
    Validate that a value is present and non-empty.

    Returns the cleaned string.
    """

    if value is None:
        raise ValueError(
            f"{field_name} is required."
        )

    value = str(value).strip()

    if not value:
        raise ValueError(
            f"{field_name} is required."
        )

    return value


def validate_email(
    email: str,
) -> bool:
    """Validate an email address."""

    if not isinstance(email, str):
        return False

    email = email.strip()

    return bool(
        EMAIL_PATTERN.fullmatch(email)
    )


def validate_indian_phone(
    phone: str,
) -> bool:
    """Validate an Indian mobile number."""

    if not isinstance(phone, str):
        return False

    phone = phone.strip()

    return bool(
        INDIAN_PHONE_PATTERN.fullmatch(phone)
    )


def validate_pan(
    pan: str,
) -> bool:
    """
    Validate the basic format of an Indian PAN.

    This validates format only, not whether the PAN
    actually exists in government records.
    """

    if not isinstance(pan, str):
        return False

    pan = pan.strip().upper()

    return bool(
        PAN_PATTERN.fullmatch(pan)
    )


def validate_aadhaar(
    aadhaar: str,
) -> bool:
    """
    Validate the basic 12-digit Aadhaar format.

    This does not verify Aadhaar against UIDAI.
    """

    if not isinstance(aadhaar, str):
        return False

    aadhaar = aadhaar.strip()

    return bool(
        AADHAAR_PATTERN.fullmatch(aadhaar)
    )


def validate_url(
    url: str,
) -> bool:
    """Validate that a URL has a valid HTTP/HTTPS scheme."""

    if not isinstance(url, str):
        return False

    url = url.strip()

    if not url:
        return False

    try:
        parsed = urlparse(url)

        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.netloc)
        )

    except Exception:
        return False