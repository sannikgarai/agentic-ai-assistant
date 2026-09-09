"""
Browser automation package.

Provides:
- Browser lifecycle management
- Portal navigation
- Form filling
- File uploading
- Application submission
- User approval workflow
"""

from app.automation.approval import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalStatus,
)
from app.automation.browser import (
    BrowserManager,
)
from app.automation.form_filler import (
    FieldFillResult,
    FormFiller,
)
from app.automation.portal import (
    PortalManager,
    PortalResult,
)
from app.automation.submission import (
    SubmissionResult,
    SubmissionManager,
)
from app.automation.upload_handler import (
    UploadResult,
    UploadHandler,
)

__all__ = [
    "BrowserManager",
    "FormFiller",
    "FieldFillResult",
    "PortalManager",
    "PortalResult",
    "UploadHandler",
    "UploadResult",
    "SubmissionManager",
    "SubmissionResult",
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalStatus",
]