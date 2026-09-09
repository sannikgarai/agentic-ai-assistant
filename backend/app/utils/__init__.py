"""
General application utilities.
"""

from app.utils.file_utils import (
    ALLOWED_FILE_EXTENSIONS,
    get_file_extension,
    get_file_size,
    is_allowed_file,
    sanitize_filename,
    save_upload_file,
)
from app.utils.validators import (
    validate_email,
    validate_indian_phone,
    validate_pan,
    validate_aadhaar,
    validate_url,
    validate_required,
)

__all__ = [
    "ALLOWED_FILE_EXTENSIONS",
    "get_file_extension",
    "get_file_size",
    "is_allowed_file",
    "sanitize_filename",
    "save_upload_file",
    "validate_email",
    "validate_indian_phone",
    "validate_pan",
    "validate_aadhaar",
    "validate_url",
    "validate_required",
]