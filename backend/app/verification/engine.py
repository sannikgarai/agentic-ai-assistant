"""
End-to-end verification engine.

Combines:
- Field matching
- Mismatch detection
- Eligibility checking

The engine is deterministic and does not itself invent
eligibility rules. Eligibility rules should be supplied by
an authoritative source such as the RAG pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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


@dataclass
class VerificationResult:
    """Complete verification result."""

    success: bool
    verified: bool
    confidence: float

    matched_fields: list[str] = field(
        default_factory=list
    )

    mismatched_fields: list[str] = field(
        default_factory=list
    )

    missing_fields: list[str] = field(
        default_factory=list
    )

    matches: list[FieldMatch] = field(
        default_factory=list
    )

    mismatches: list[Mismatch] = field(
        default_factory=list
    )

    eligibility: EligibilityResult | None = None

    reasons: list[str] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert verification result to dictionary."""

        return {
            "success": self.success,
            "verified": self.verified,
            "confidence": self.confidence,
            "matched_fields": self.matched_fields,
            "mismatched_fields": self.mismatched_fields,
            "missing_fields": self.missing_fields,
            "matches": [
                match.to_dict()
                for match in self.matches
            ],
            "mismatches": [
                mismatch.to_dict()
                for mismatch in self.mismatches
            ],
            "eligibility": (
                self.eligibility.to_dict()
                if self.eligibility is not None
                else None
            ),
            "reasons": self.reasons,
            "metadata": self.metadata,
        }


class VerificationEngine:
    """Main verification service."""

    def __init__(
        self,
        field_matcher: FieldMatcher | None = None,
        mismatch_detector: MismatchDetector | None = None,
        eligibility_checker: EligibilityChecker | None = None,
    ):
        self.field_matcher = (
            field_matcher
            if field_matcher is not None
            else FieldMatcher()
        )

        self.mismatch_detector = (
            mismatch_detector
            if mismatch_detector is not None
            else MismatchDetector()
        )

        self.eligibility_checker = (
            eligibility_checker
            if eligibility_checker is not None
            else EligibilityChecker()
        )

    def verify_fields(
        self,
        source_a: dict[str, Any],
        source_b: dict[str, Any],
        fields: list[str] | None = None,
    ) -> VerificationResult:
        """
        Verify fields between two sources.

        Returns matching, mismatching, and missing fields
        together with an aggregate confidence score.
        """

        if not isinstance(source_a, dict):
            raise TypeError(
                "source_a must be a dictionary."
            )

        if not isinstance(source_b, dict):
            raise TypeError(
                "source_b must be a dictionary."
            )

        matches = self.field_matcher.match_fields(
            fields_a=source_a,
            fields_b=source_b,
            fields=fields,
        )

        mismatches = self.mismatch_detector.detect(
            matches
        )

        matched_fields = (
            self.mismatch_detector.get_matching_fields(
                matches
            )
        )

        mismatching_fields = (
            self.mismatch_detector.get_mismatching_fields(
                matches
            )
        )

        missing_fields = self._get_missing_fields(
            mismatches
        )

        confidence = self._calculate_confidence(
            matches
        )

        verified = (
            len(matches) > 0
            and not mismatching_fields
            and not missing_fields
        )

        reasons = self._build_field_reasons(
            verified=verified,
            mismatching_fields=mismatching_fields,
            missing_fields=missing_fields,
            matches=matches,
        )

        severity_counts = self._severity_counts(
            mismatches
        )

        return VerificationResult(
            success=True,
            verified=verified,
            confidence=confidence,
            matched_fields=matched_fields,
            mismatched_fields=mismatching_fields,
            missing_fields=missing_fields,
            matches=matches,
            mismatches=mismatches,
            reasons=reasons,
            metadata={
                "comparison_type": "field_comparison",
                "total_fields": len(matches),
                "matched_count": len(
                    matched_fields
                ),
                "mismatched_count": len(
                    mismatching_fields
                ),
                "missing_count": len(
                    missing_fields
                ),
                "severity_counts": severity_counts,
            },
        )

    def verify_with_eligibility(
        self,
        source_a: dict[str, Any],
        source_b: dict[str, Any],
        eligibility_data: dict[str, Any],
        fields: list[str] | None = None,
    ) -> VerificationResult:
        """
        Verify fields and evaluate eligibility.

        Expected eligibility_data format:

        {
            "rules": [
                {
                    "id": "age_limit",
                    "field": "age",
                    "operator": "greater_than_or_equal",
                    "value": 18,
                    "description": "Applicant must be at least 18."
                }
            ]
        }

        The applicant data used for eligibility is source_a.
        """

        if not isinstance(
            eligibility_data,
            dict,
        ):
            raise TypeError(
                "eligibility_data must be a dictionary."
            )

        verification = self.verify_fields(
            source_a=source_a,
            source_b=source_b,
            fields=fields,
        )

        rules = eligibility_data.get(
            "rules",
            [],
        )

        if rules is None:
            rules = []

        if not isinstance(
            rules,
            list,
        ):
            raise TypeError(
                "eligibility_data['rules'] must be a list."
            )

        eligibility = (
            self.eligibility_checker.check(
                applicant=source_a,
                rules=rules,
            )
        )

        reasons = list(
            verification.reasons
        )

        reasons.extend(
            eligibility.reasons
        )

        reasons = self._unique_reasons(
            reasons
        )

        # Identity/document verification and
        # eligibility are separate requirements.
        verified = (
            verification.verified
            and eligibility.eligible
        )

        # Keep field confidence as the primary
        # document/data matching confidence.
        field_confidence = verification.confidence

        # Eligibility contributes only when rules
        # were actually supplied and evaluated.
        if rules and eligibility.metadata.get(
            "evaluated_rules",
            0,
        ) > 0:
            eligibility_confidence = (
                eligibility.score
            )

            confidence = (
                field_confidence
                * 0.7
                + eligibility_confidence
                * 0.3
            )
        else:
            confidence = field_confidence

        missing_fields = sorted(
            set(
                verification.missing_fields
                + eligibility.missing_information
            )
        )

        metadata = {
            "comparison_type": (
                "field_comparison_and_eligibility"
            ),
            "field_confidence": (
                verification.confidence
            ),
            "eligibility_score": (
                eligibility.score
            ),
            "eligibility_status": (
                eligibility.metadata.get(
                    "status"
                )
            ),
            "total_fields": len(
                verification.matches
            ),
            "total_eligibility_rules": len(
                rules
            ),
        }

        return VerificationResult(
            success=True,
            verified=verified,
            confidence=round(
                max(
                    0.0,
                    min(
                        1.0,
                        confidence,
                    ),
                ),
                4,
            ),
            matched_fields=verification.matched_fields,
            mismatched_fields=verification.mismatched_fields,
            missing_fields=missing_fields,
            matches=verification.matches,
            mismatches=verification.mismatches,
            eligibility=eligibility,
            reasons=reasons,
            metadata=metadata,
        )

    @staticmethod
    def _get_missing_fields(
        mismatches: list[Mismatch],
    ) -> list[str]:
        """Extract unique missing field names."""

        missing_types = {
            "missing_source_a",
            "missing_source_b",
            "missing_both",
        }

        return sorted(
            {
                mismatch.field_name
                for mismatch in mismatches
                if mismatch.mismatch_type
                in missing_types
            }
        )

    @staticmethod
    def _calculate_confidence(
        matches: list[FieldMatch],
    ) -> float:
        """
        Calculate aggregate field-match confidence.

        This represents similarity between supplied fields;
        it is not proof of document authenticity.
        """

        if not matches:
            return 0.0

        similarity_sum = sum(
            max(
                0.0,
                min(
                    1.0,
                    float(match.similarity),
                ),
            )
            for match in matches
        )

        average = (
            similarity_sum / len(matches)
        )

        return round(
            max(
                0.0,
                min(
                    1.0,
                    average,
                ),
            ),
            4,
        )

    @staticmethod
    def _build_field_reasons(
        verified: bool,
        mismatching_fields: list[str],
        missing_fields: list[str],
        matches: list[FieldMatch],
    ) -> list[str]:
        """Build human-readable field verification reasons."""

        reasons: list[str] = []

        if not matches:
            reasons.append(
                "No fields were available for comparison."
            )
            return reasons

        if verified:
            reasons.append(
                "All supplied comparison fields matched."
            )
            return reasons

        if mismatching_fields:
            reasons.append(
                "One or more field values do not match."
            )

        if missing_fields:
            reasons.append(
                "One or more comparison fields are missing."
            )

        return reasons

    @staticmethod
    def _severity_counts(
        mismatches: list[Mismatch],
    ) -> dict[str, int]:
        """Count mismatches by severity."""

        counts = {
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for mismatch in mismatches:
            severity = mismatch.severity.lower()

            if severity in counts:
                counts[severity] += 1

        return counts

    @staticmethod
    def _unique_reasons(
        reasons: list[str],
    ) -> list[str]:
        """Remove duplicate reasons while preserving order."""

        result: list[str] = []
        seen: set[str] = set()

        for reason in reasons:
            if reason not in seen:
                seen.add(reason)
                result.append(reason)

        return result