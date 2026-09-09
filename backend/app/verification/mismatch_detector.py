"""
Mismatch detection.

Identifies:
- Missing fields
- Mismatched fields
- Matching fields
- Severity of detected inconsistencies
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.verification.field_matcher import FieldMatch


@dataclass
class Mismatch:
    """Represents a detected mismatch or missing field."""

    field_name: str
    value_a: Any
    value_b: Any
    mismatch_type: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        """Convert mismatch to dictionary."""

        return {
            "field_name": self.field_name,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "mismatch_type": self.mismatch_type,
            "severity": self.severity,
            "message": self.message,
        }


class MismatchDetector:
    """Detect inconsistencies between structured field sets."""

    DEFAULT_CRITICAL_FIELDS = {
        "name",
        "full_name",
        "pan",
        "aadhaar",
        "date_of_birth",
        "dob",
        "father_name",
        "mother_name",
    }

    DEFAULT_HIGH_FIELDS = {
        "account_number",
        "passport_number",
        "voter_id",
        "driving_license",
        "certificate_number",
        "application_number",
    }

    def __init__(
        self,
        critical_fields: set[str] | None = None,
        high_fields: set[str] | None = None,
    ):
        """
        Initialize the mismatch detector.

        Args:
            critical_fields: Fields where a mismatch is highly significant.
            high_fields: Important identity/application fields.
        """

        self.critical_fields = {
            field.strip().lower()
            for field in (
                critical_fields
                if critical_fields is not None
                else self.DEFAULT_CRITICAL_FIELDS
            )
        }

        self.high_fields = {
            field.strip().lower()
            for field in (
                high_fields
                if high_fields is not None
                else self.DEFAULT_HIGH_FIELDS
            )
        }

    def detect(
        self,
        matches: list[FieldMatch],
    ) -> list[Mismatch]:
        """
        Convert field comparison results into mismatch records.

        Matching fields are ignored. Missing and mismatched fields
        are returned as Mismatch objects.
        """

        mismatches: list[Mismatch] = []

        for match in matches:
            field_name = str(match.field_name).strip()
            normalized_field = field_name.lower()

            value_a_missing = self._is_missing(match.value_a)
            value_b_missing = self._is_missing(match.value_b)

            # Both sources are missing.
            if value_a_missing and value_b_missing:
                mismatches.append(
                    Mismatch(
                        field_name=field_name,
                        value_a=match.value_a,
                        value_b=match.value_b,
                        mismatch_type="missing_both",
                        severity=self._severity(
                            normalized_field
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "is missing from both sources."
                        ),
                    )
                )
                continue

            # Source A is missing.
            if value_a_missing:
                mismatches.append(
                    Mismatch(
                        field_name=field_name,
                        value_a=match.value_a,
                        value_b=match.value_b,
                        mismatch_type="missing_source_a",
                        severity=self._severity(
                            normalized_field
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "is missing from source A."
                        ),
                    )
                )
                continue

            # Source B is missing.
            if value_b_missing:
                mismatches.append(
                    Mismatch(
                        field_name=field_name,
                        value_a=match.value_a,
                        value_b=match.value_b,
                        mismatch_type="missing_source_b",
                        severity=self._severity(
                            normalized_field
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "is missing from source B."
                        ),
                    )
                )
                continue

            # Both values exist but do not match.
            if not match.matched:
                mismatches.append(
                    Mismatch(
                        field_name=field_name,
                        value_a=match.value_a,
                        value_b=match.value_b,
                        mismatch_type="value_mismatch",
                        severity=self._severity(
                            normalized_field
                        ),
                        message=(
                            f"Field '{field_name}' "
                            "contains different values."
                        ),
                    )
                )

        return mismatches

    def get_missing_fields(
        self,
        source: dict[str, Any],
        required_fields: list[str],
    ) -> list[str]:
        """
        Return required fields missing from a source.

        Handles both missing keys and empty values.
        Field names are matched case-insensitively.
        """

        normalized_source = {
            str(key).strip().lower(): value
            for key, value in source.items()
        }

        missing: list[str] = []

        for field_name in required_fields:
            normalized_field = str(field_name).strip().lower()

            if normalized_field not in normalized_source:
                missing.append(field_name)
                continue

            if self._is_missing(
                normalized_source[normalized_field]
            ):
                missing.append(field_name)

        return missing

    def get_matching_fields(
        self,
        matches: list[FieldMatch],
    ) -> list[str]:
        """Return names of fields that matched."""

        return [
            match.field_name
            for match in matches
            if match.matched
        ]

    def get_mismatching_fields(
        self,
        matches: list[FieldMatch],
    ) -> list[str]:
        """
        Return names of fields whose values exist but differ.

        Missing fields are deliberately excluded.
        """

        return [
            match.field_name
            for match in matches
            if not match.matched
            and not self._is_missing(match.value_a)
            and not self._is_missing(match.value_b)
        ]

    def get_missing_from_a(
        self,
        matches: list[FieldMatch],
    ) -> list[str]:
        """Return fields missing from source A."""

        return [
            match.field_name
            for match in matches
            if self._is_missing(match.value_a)
            and not self._is_missing(match.value_b)
        ]

    def get_missing_from_b(
        self,
        matches: list[FieldMatch],
    ) -> list[str]:
        """Return fields missing from source B."""

        return [
            match.field_name
            for match in matches
            if not self._is_missing(match.value_b)
            and self._is_missing(match.value_a)
        ]

    def summarize(
        self,
        matches: list[FieldMatch],
    ) -> dict[str, Any]:
        """
        Create a compact mismatch summary.

        This is useful for the verification engine and API response.
        """

        mismatches = self.detect(matches)

        matching_fields = self.get_matching_fields(matches)
        mismatching_fields = self.get_mismatching_fields(matches)
        missing_from_a = self.get_missing_from_a(matches)
        missing_from_b = self.get_missing_from_b(matches)

        high_count = sum(
            1
            for item in mismatches
            if item.severity == "high"
        )

        medium_count = sum(
            1
            for item in mismatches
            if item.severity == "medium"
        )

        low_count = sum(
            1
            for item in mismatches
            if item.severity == "low"
        )

        return {
            "total_fields": len(matches),
            "matching_fields": matching_fields,
            "mismatching_fields": mismatching_fields,
            "missing_from_a": missing_from_a,
            "missing_from_b": missing_from_b,
            "mismatches": [
                mismatch.to_dict()
                for mismatch in mismatches
            ],
            "severity_counts": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count,
            },
            "has_mismatch": bool(mismatching_fields),
            "has_missing_fields": bool(
                missing_from_a or missing_from_b
            ),
            "requires_review": any(
                mismatch.severity == "high"
                for mismatch in mismatches
            ),
        }

    def _severity(
        self,
        field_name: str,
    ) -> str:
        """Determine mismatch severity."""

        normalized_field = field_name.strip().lower()

        if normalized_field in self.critical_fields:
            return "high"

        if normalized_field in self.high_fields:
            return "high"

        return "medium"

    @staticmethod
    def _is_missing(value: Any) -> bool:
        """Return True when a field value is missing or empty."""

        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        return False