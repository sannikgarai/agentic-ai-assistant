"""
Field matching utilities.

Compares structured fields extracted from documents or supplied
by the user/application.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any


@dataclass
class FieldMatch:
    """Represents the comparison result of one field."""

    field_name: str
    value_a: Any
    value_b: Any
    matched: bool
    similarity: float
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert match result to a dictionary."""

        return {
            "field_name": self.field_name,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "matched": self.matched,
            "similarity": self.similarity,
            "reason": self.reason,
        }


class FieldMatcher:
    """Compare structured fields using normalized values."""

    DEFAULT_EXACT_FIELDS = {
        "pan",
        "aadhaar",
        "phone",
        "email",
        "account_number",
        "application_number",
        "certificate_number",
        "roll_number",
        "passport_number",
        "voter_id",
        "driving_license",
    }

    DEFAULT_TEXT_FIELDS = {
        "name",
        "full_name",
        "father_name",
        "mother_name",
        "address",
        "district",
        "state",
        "village",
        "occupation",
    }

    DEFAULT_DATE_FIELDS = {
        "dob",
        "date_of_birth",
        "birth_date",
        "issue_date",
        "expiry_date",
        "date",
    }

    def __init__(
        self,
        exact_fields: set[str] | None = None,
        text_fields: set[str] | None = None,
        date_fields: set[str] | None = None,
        text_match_threshold: float = 0.90,
    ):
        self.exact_fields = {
            field.lower()
            for field in (
                exact_fields
                if exact_fields is not None
                else self.DEFAULT_EXACT_FIELDS
            )
        }

        self.text_fields = {
            field.lower()
            for field in (
                text_fields
                if text_fields is not None
                else self.DEFAULT_TEXT_FIELDS
            )
        }

        self.date_fields = {
            field.lower()
            for field in (
                date_fields
                if date_fields is not None
                else self.DEFAULT_DATE_FIELDS
            )
        }

        if not 0.0 <= text_match_threshold <= 1.0:
            raise ValueError(
                "text_match_threshold must be between 0 and 1."
            )

        self.text_match_threshold = text_match_threshold

    def match_field(
        self,
        field_name: str,
        value_a: Any,
        value_b: Any,
    ) -> FieldMatch:
        """Compare two values for a specific field."""

        normalized_field = str(field_name).strip().lower()

        if value_a is None or value_b is None:
            return FieldMatch(
                field_name=field_name,
                value_a=value_a,
                value_b=value_b,
                matched=False,
                similarity=0.0,
                reason="One or both values are missing.",
            )

        normalized_a = self.normalize(
            normalized_field,
            value_a,
        )

        normalized_b = self.normalize(
            normalized_field,
            value_b,
        )

        if not normalized_a or not normalized_b:
            return FieldMatch(
                field_name=field_name,
                value_a=value_a,
                value_b=value_b,
                matched=False,
                similarity=0.0,
                reason="One or both values are empty.",
            )

        # Exact fields
        if normalized_field in self.exact_fields:
            matched = normalized_a == normalized_b

            return FieldMatch(
                field_name=field_name,
                value_a=value_a,
                value_b=value_b,
                matched=matched,
                similarity=1.0 if matched else 0.0,
                reason=(
                    "Exact match."
                    if matched
                    else "Exact values differ."
                ),
            )

        # Date fields
        if normalized_field in self.date_fields:
            matched = normalized_a == normalized_b

            return FieldMatch(
                field_name=field_name,
                value_a=value_a,
                value_b=value_b,
                matched=matched,
                similarity=1.0 if matched else 0.0,
                reason=(
                    "Dates match."
                    if matched
                    else "Dates differ."
                ),
            )

        # Text fields and unknown fields
        similarity = self._text_similarity(
            normalized_a,
            normalized_b,
        )

        matched = similarity >= self.text_match_threshold

        if matched:
            reason = "Values are sufficiently similar."
        else:
            reason = "Values differ."

        return FieldMatch(
            field_name=field_name,
            value_a=value_a,
            value_b=value_b,
            matched=matched,
            similarity=round(similarity, 4),
            reason=reason,
        )

    def match_fields(
        self,
        fields_a: dict[str, Any],
        fields_b: dict[str, Any],
        fields: list[str] | None = None,
    ) -> list[FieldMatch]:
        """Compare multiple fields."""

        if not isinstance(fields_a, dict):
            raise TypeError("fields_a must be a dictionary.")

        if not isinstance(fields_b, dict):
            raise TypeError("fields_b must be a dictionary.")

        normalized_a = {
            str(key).strip().lower(): value
            for key, value in fields_a.items()
        }

        normalized_b = {
            str(key).strip().lower(): value
            for key, value in fields_b.items()
        }

        if fields is None:
            field_names = sorted(
                set(normalized_a.keys())
                | set(normalized_b.keys())
            )
        else:
            field_names = [
                str(field).strip().lower()
                for field in fields
            ]

        results: list[FieldMatch] = []

        for field_name in field_names:
            result = self.match_field(
                field_name=field_name,
                value_a=normalized_a.get(field_name),
                value_b=normalized_b.get(field_name),
            )

            results.append(result)

        return results

    def match_and_summarize(
        self,
        fields_a: dict[str, Any],
        fields_b: dict[str, Any],
        fields: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Compare fields and return both individual results
        and an overall verification summary.
        """

        matches = self.match_fields(
            fields_a=fields_a,
            fields_b=fields_b,
            fields=fields,
        )

        total = len(matches)
        matched = sum(
            1 for result in matches
            if result.matched
        )
        mismatched = sum(
            1 for result in matches
            if not result.matched
            and result.value_a is not None
            and result.value_b is not None
        )
        missing = sum(
            1 for result in matches
            if result.value_a is None
            or result.value_b is None
        )

        average_similarity = (
            sum(result.similarity for result in matches)
            / total
            if total
            else 0.0
        )

        return {
            "matches": [
                result.to_dict()
                for result in matches
            ],
            "total_fields": total,
            "matched_fields": matched,
            "mismatched_fields": mismatched,
            "missing_fields": missing,
            "average_similarity": round(
                average_similarity,
                4,
            ),
            "verification_status": self._get_status(
                total=total,
                matched=matched,
                mismatched=mismatched,
                missing=missing,
            ),
        }

    @classmethod
    def normalize(
        cls,
        field_name: str,
        value: Any,
    ) -> str:
        """Normalize a field value for comparison."""

        if value is None:
            return ""

        text = str(value).strip().lower()

        if not text:
            return ""

        field = field_name.strip().lower()

        # -------------------------------------------------
        # Email
        # -------------------------------------------------
        if field == "email":
            return text.replace(" ", "")

        # -------------------------------------------------
        # Phone numbers
        # -------------------------------------------------
        if field == "phone":
            digits = re.sub(r"\D", "", text)

            # Normalize Indian numbers such as:
            # 9876543210
            # +91 9876543210
            # 919876543210
            if len(digits) == 12 and digits.startswith("91"):
                digits = digits[2:]

            return digits

        # -------------------------------------------------
        # Identifier fields
        # -------------------------------------------------
        if field in {
            "aadhaar",
            "pan",
            "account_number",
            "application_number",
            "certificate_number",
            "roll_number",
            "passport_number",
            "voter_id",
            "driving_license",
        }:
            return re.sub(
                r"[\s\-_]",
                "",
                text,
            )

        # -------------------------------------------------
        # Date fields
        # -------------------------------------------------
        if field in cls.DEFAULT_DATE_FIELDS:
            normalized_date = cls._normalize_date(text)

            if normalized_date:
                return normalized_date

        # -------------------------------------------------
        # Names and addresses
        # -------------------------------------------------
        if field in {
            "name",
            "full_name",
            "father_name",
            "mother_name",
            "address",
            "district",
            "state",
            "village",
            "occupation",
        }:
            text = re.sub(
                r"[^\w\s]",
                "",
                text,
                flags=re.UNICODE,
            )

            text = re.sub(
                r"\s+",
                " ",
                text,
            )

        return text.strip()

    @staticmethod
    def _normalize_date(value: str) -> str:
        """Normalize common date formats to YYYY-MM-DD."""

        value = value.strip()

        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y.%m.%d",
            "%d/%m/%y",
            "%d-%m-%y",
            "%d.%m.%y",
        ]

        for date_format in formats:
            try:
                parsed = datetime.strptime(
                    value,
                    date_format,
                )

                return parsed.strftime("%Y-%m-%d")

            except ValueError:
                continue

        return ""

    @staticmethod
    def _text_similarity(
        value_a: str,
        value_b: str,
    ) -> float:
        """Calculate token and character-level similarity."""

        if value_a == value_b:
            return 1.0

        tokens_a = set(value_a.split())
        tokens_b = set(value_b.split())

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        jaccard = (
            len(intersection) / len(union)
            if union
            else 0.0
        )

        sequence_similarity = SequenceMatcher(
            None,
            value_a,
            value_b,
        ).ratio()

        return max(
            jaccard,
            sequence_similarity,
        )

    @staticmethod
    def _get_status(
        total: int,
        matched: int,
        mismatched: int,
        missing: int,
    ) -> str:
        """Determine an overall verification status."""

        if total == 0:
            return "no_data"

        if mismatched > 0:
            return "mismatch"

        if missing > 0:
            return "incomplete"

        if matched == total:
            return "verified"

        return "review_required"