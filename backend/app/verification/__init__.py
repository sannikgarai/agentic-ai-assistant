"""
Verification package.

Provides:
- Field matching
- Mismatch detection
- Eligibility checking
- Verification engine
"""

from backend.app.verification.engine import (
    VerificationEngine,
)
from backend.app.verification.eligibility_checker import (
    EligibilityChecker,
    EligibilityResult,
)
from backend.app.verification.field_matcher import (
    FieldMatch,
    FieldMatcher,
)
from backend.app.verification.mismatch_detector import (
    Mismatch,
    MismatchDetector,
)

__all__ = [
    "FieldMatch",
    "FieldMatcher",
    "Mismatch",
    "MismatchDetector",
    "EligibilityChecker",
    "EligibilityResult",
    "VerificationEngine",
]