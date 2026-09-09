"""
Eligibility checking.

Evaluates applicant data against supplied eligibility rules.

Rules should come from authoritative sources such as
government scheme documents retrieved through the RAG system.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass
class EligibilityResult:
    """Result of an eligibility evaluation."""

    eligible: bool
    score: float
    passed_rules: list[str] = field(default_factory=list)
    failed_rules: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "eligible": self.eligible,
            "score": self.score,
            "passed_rules": self.passed_rules,
            "failed_rules": self.failed_rules,
            "missing_information": self.missing_information,
            "reasons": self.reasons,
            "metadata": self.metadata,
        }


class EligibilityChecker:
    """
    Rule-based eligibility checker.

    Supported operators:
    - equals
    - not_equals
    - in
    - not_in
    - greater_than
    - greater_than_or_equal
    - less_than
    - less_than_or_equal
    - exists
    - contains
    - not_contains
    - is_true
    - is_false
    """

    SUPPORTED_OPERATORS = {
        "equals",
        "not_equals",
        "in",
        "not_in",
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "exists",
        "contains",
        "not_contains",
        "is_true",
        "is_false",
    }

    def check(
        self,
        applicant: dict[str, Any],
        rules: list[dict[str, Any]],
    ) -> EligibilityResult:
        """Evaluate applicant data against eligibility rules."""

        if not isinstance(applicant, dict):
            raise TypeError(
                "applicant must be a dictionary."
            )

        if not rules:
            return EligibilityResult(
                eligible=False,
                score=0.0,
                reasons=[
                    "No eligibility rules were supplied."
                ],
                metadata={
                    "status": "rules_missing",
                    "total_rules": 0,
                    "evaluated_rules": 0,
                },
            )

        normalized_applicant = {
            str(key).strip().lower(): value
            for key, value in applicant.items()
        }

        passed: list[str] = []
        failed: list[str] = []
        missing: list[str] = []
        reasons: list[str] = []

        evaluated_count = 0
        invalid_rules = 0

        for index, rule in enumerate(
            rules,
            start=1,
        ):
            if not isinstance(rule, dict):
                invalid_rules += 1
                reasons.append(
                    f"Rule {index} is invalid."
                )
                continue

            field_name = str(
                rule.get("field", "")
            ).strip()

            operator = str(
                rule.get(
                    "operator",
                    "equals",
                )
            ).strip().lower()

            expected = rule.get("value")

            rule_id = str(
                rule.get(
                    "id",
                    f"rule_{index}",
                )
            ).strip()

            description = str(
                rule.get(
                    "description",
                    f"Requirement for {field_name}.",
                )
            ).strip()

            if not field_name:
                invalid_rules += 1
                reasons.append(
                    f"Rule '{rule_id}' has no field."
                )
                continue

            if operator not in self.SUPPORTED_OPERATORS:
                invalid_rules += 1
                reasons.append(
                    f"Rule '{rule_id}' uses unsupported "
                    f"operator '{operator}'."
                )
                continue

            normalized_field = field_name.lower()

            field_exists = (
                normalized_field
                in normalized_applicant
            )

            actual = normalized_applicant.get(
                normalized_field
            )

            # -------------------------------------------------
            # EXISTS does not require a normal value.
            # -------------------------------------------------
            if operator == "exists":
                evaluated_count += 1

                passed_rule = (
                    field_exists
                    and not self._is_empty(actual)
                )

                if passed_rule:
                    passed.append(rule_id)
                else:
                    failed.append(rule_id)
                    reasons.append(description)

                continue

            # -------------------------------------------------
            # Boolean rules can work with an explicitly
            # supplied boolean value.
            # -------------------------------------------------
            if operator in {
                "is_true",
                "is_false",
            }:
                if not field_exists or self._is_empty(actual):
                    missing.append(field_name)
                    reasons.append(
                        f"Missing information: {field_name}."
                    )
                    continue

                evaluated_count += 1

                passed_rule = self._evaluate(
                    actual,
                    operator,
                    expected,
                )

                if passed_rule:
                    passed.append(rule_id)
                else:
                    failed.append(rule_id)
                    reasons.append(description)

                continue

            # -------------------------------------------------
            # Other operators require applicant data.
            # -------------------------------------------------
            if not field_exists or self._is_empty(actual):
                missing.append(field_name)
                reasons.append(
                    f"Missing information: {field_name}."
                )
                continue

            evaluated_count += 1

            try:
                passed_rule = self._evaluate(
                    actual,
                    operator,
                    expected,
                )

            except (TypeError, ValueError, InvalidOperation):
                passed_rule = False
                reasons.append(
                    f"Unable to evaluate rule "
                    f"'{rule_id}' for field "
                    f"'{field_name}'."
                )

            if passed_rule:
                passed.append(rule_id)
            else:
                failed.append(rule_id)

                if description not in reasons:
                    reasons.append(description)

        unique_missing = sorted(
            set(missing)
        )

        # Eligibility requires:
        # 1. At least one valid/evaluated rule
        # 2. No missing required information
        # 3. No failed rules
        eligible = (
            evaluated_count > 0
            and not unique_missing
            and not failed
            and invalid_rules == 0
        )

        score = (
            len(passed) / evaluated_count
            if evaluated_count
            else 0.0
        )

        if unique_missing:
            status = "insufficient_information"
        elif invalid_rules > 0:
            status = "rules_invalid"
        elif failed:
            status = "not_eligible"
        elif eligible:
            status = "eligible"
        else:
            status = "review_required"

        return EligibilityResult(
            eligible=eligible,
            score=round(score, 4),
            passed_rules=passed,
            failed_rules=failed,
            missing_information=unique_missing,
            reasons=self._unique_reasons(reasons),
            metadata={
                "status": status,
                "total_rules": len(rules),
                "evaluated_rules": evaluated_count,
                "invalid_rules": invalid_rules,
                "passed_count": len(passed),
                "failed_count": len(failed),
                "missing_count": len(unique_missing),
            },
        )

    def _evaluate(
        self,
        actual: Any,
        operator: str,
        expected: Any,
    ) -> bool:
        """Evaluate a single eligibility rule."""

        if operator == "exists":
            return not self._is_empty(actual)

        if operator == "equals":
            return self._values_equal(
                actual,
                expected,
            )

        if operator == "not_equals":
            return not self._values_equal(
                actual,
                expected,
            )

        if operator == "in":
            if not isinstance(
                expected,
                (list, tuple, set),
            ):
                raise ValueError(
                    "'in' requires a collection."
                )

            return any(
                self._values_equal(
                    actual,
                    item,
                )
                for item in expected
            )

        if operator == "not_in":
            if not isinstance(
                expected,
                (list, tuple, set),
            ):
                raise ValueError(
                    "'not_in' requires a collection."
                )

            return all(
                not self._values_equal(
                    actual,
                    item,
                )
                for item in expected
            )

        if operator in {
            "greater_than",
            "greater_than_or_equal",
            "less_than",
            "less_than_or_equal",
        }:
            return self._compare(
                actual,
                expected,
                operator,
            )

        if operator == "contains":
            return self._contains(
                actual,
                expected,
            )

        if operator == "not_contains":
            return not self._contains(
                actual,
                expected,
            )

        if operator == "is_true":
            return self._to_bool(actual) is True

        if operator == "is_false":
            return self._to_bool(actual) is False

        raise ValueError(
            f"Unsupported eligibility operator: {operator}"
        )

    def _compare(
        self,
        actual: Any,
        expected: Any,
        operator: str,
    ) -> bool:
        """Perform a safe comparison."""

        actual_number = self._to_decimal(actual)
        expected_number = self._to_decimal(expected)

        if (
            actual_number is not None
            and expected_number is not None
        ):
            left = actual_number
            right = expected_number
        else:
            actual_date = self._to_date(actual)
            expected_date = self._to_date(expected)

            if (
                actual_date is not None
                and expected_date is not None
            ):
                left = actual_date
                right = expected_date
            else:
                raise ValueError(
                    "Values cannot be compared."
                )

        if operator == "greater_than":
            return left > right

        if operator == "greater_than_or_equal":
            return left >= right

        if operator == "less_than":
            return left < right

        if operator == "less_than_or_equal":
            return left <= right

        raise ValueError(
            f"Unsupported comparison operator: {operator}"
        )

    @staticmethod
    def _contains(
        actual: Any,
        expected: Any,
    ) -> bool:
        """Check whether actual contains expected."""

        if isinstance(actual, str):
            return (
                str(expected).strip().lower()
                in actual.strip().lower()
            )

        if isinstance(
            actual,
            (list, tuple, set),
        ):
            return any(
                EligibilityChecker._values_equal(
                    item,
                    expected,
                )
                for item in actual
            )

        if isinstance(actual, dict):
            return str(expected).strip().lower() in {
                str(key).strip().lower()
                for key in actual.keys()
            }

        return False

    @classmethod
    def _values_equal(
        cls,
        value_a: Any,
        value_b: Any,
    ) -> bool:
        """Compare two values after normalization."""

        if isinstance(value_a, bool) or isinstance(
            value_b,
            bool,
        ):
            return cls._to_bool(value_a) == cls._to_bool(
                value_b
            )

        number_a = cls._to_decimal(value_a)
        number_b = cls._to_decimal(value_b)

        if (
            number_a is not None
            and number_b is not None
        ):
            return number_a == number_b

        date_a = cls._to_date(value_a)
        date_b = cls._to_date(value_b)

        if (
            date_a is not None
            and date_b is not None
        ):
            return date_a == date_b

        return (
            cls._normalize(value_a)
            == cls._normalize(value_b)
        )

    @staticmethod
    def _normalize(value: Any) -> str:
        """Normalize a value for text comparison."""

        if value is None:
            return ""

        return str(value).strip().casefold()

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """Return True when a value is missing or empty."""

        if value is None:
            return True

        if isinstance(value, str):
            return not value.strip()

        return False

    @staticmethod
    def _to_decimal(
        value: Any,
    ) -> Decimal | None:
        """Convert a value to Decimal when possible."""

        if isinstance(value, bool):
            return None

        if isinstance(
            value,
            (int, float, Decimal),
        ):
            try:
                return Decimal(str(value))
            except InvalidOperation:
                return None

        if isinstance(value, str):
            text = value.strip()

            if not text:
                return None

            # Remove common currency formatting.
            cleaned = (
                text.replace(",", "")
                .replace("₹", "")
                .replace("$", "")
                .strip()
            )

            try:
                return Decimal(cleaned)
            except InvalidOperation:
                return None

        return None

    @staticmethod
    def _to_date(
        value: Any,
    ) -> date | None:
        """Convert common date representations."""

        if isinstance(value, datetime):
            return value.date()

        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            return None

        text = value.strip()

        if not text:
            return None

        formats = (
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d.%m.%Y",
            "%Y/%m/%d",
            "%Y.%m.%d",
        )

        for date_format in formats:
            try:
                return datetime.strptime(
                    text,
                    date_format,
                ).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _to_bool(
        value: Any,
    ) -> bool | None:
        """Convert common boolean representations."""

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().casefold()

            if normalized in {
                "true",
                "yes",
                "y",
                "1",
                "eligible",
            }:
                return True

            if normalized in {
                "false",
                "no",
                "n",
                "0",
                "not eligible",
            }:
                return False

        if isinstance(value, (int, float)):
            if value == 1:
                return True

            if value == 0:
                return False

        return None

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