"""
Document information extractor.

Extracts common structured fields such as:
- Name
- Father's name
- Mother's name
- Date of birth
- Annual income
- Aadhaar-like numbers
- PAN-like numbers
- Phone numbers
- Email addresses
- Dates
- Addresses

This is a baseline pattern-based extractor. It must not be
treated as an authoritative identity verification mechanism.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ExtractedField:
    """One extracted document field."""

    field_name: str
    value: str
    confidence: float
    source: str = "regex"

    def to_dict(self) -> dict[str, Any]:
        """Convert field to dictionary."""

        return {
            "field_name": self.field_name,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
        }


@dataclass
class ExtractionResult:
    """Structured document extraction result."""

    fields: dict[str, Any] = field(
        default_factory=dict
    )

    extracted_fields: list[ExtractedField] = field(
        default_factory=list
    )

    raw_text: str = ""

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert extraction result to dictionary."""

        return {
            "fields": self.fields,
            "extracted_fields": [
                item.to_dict()
                for item in self.extracted_fields
            ],
            "raw_text": self.raw_text,
            "metadata": self.metadata,
        }


class DocumentExtractor:
    """Extract structured information from document text."""

    def extract(
        self,
        text: str,
        document_type: str = "unknown",
    ) -> ExtractionResult:
        """Extract known fields from document text."""

        text = text or ""
        document_type = (
            document_type or "unknown"
        ).strip().lower()

        if not text.strip():
            return ExtractionResult(
                raw_text=text,
                metadata={
                    "document_type": document_type,
                    "method": "pattern_based",
                    "message": (
                        "No text available for extraction."
                    ),
                },
            )

        fields: dict[str, Any] = {}

        extracted_fields: list[
            ExtractedField
        ] = []

        # --------------------------------------------------
        # Contact information
        # --------------------------------------------------

        self._extract_email(
            text,
            fields,
            extracted_fields,
        )

        self._extract_phone(
            text,
            fields,
            extracted_fields,
        )

        # --------------------------------------------------
        # Identity numbers
        # --------------------------------------------------

        self._extract_pan(
            text,
            fields,
            extracted_fields,
        )

        self._extract_aadhaar(
            text,
            fields,
            extracted_fields,
        )

        # --------------------------------------------------
        # Dates
        # --------------------------------------------------

        self._extract_dates(
            text,
            fields,
            extracted_fields,
        )

        self._extract_date_of_birth(
            text,
            fields,
            extracted_fields,
        )

        # --------------------------------------------------
        # Financial information
        # --------------------------------------------------

        self._extract_income(
            text,
            fields,
            extracted_fields,
        )

        # --------------------------------------------------
        # Named fields
        # --------------------------------------------------

        self._extract_named_fields(
            text,
            fields,
            extracted_fields,
        )

        # --------------------------------------------------
        # Document-specific fields
        # --------------------------------------------------

        self._extract_document_specific_fields(
            text,
            document_type,
            fields,
            extracted_fields,
        )

        return ExtractionResult(
            fields=fields,
            extracted_fields=extracted_fields,
            raw_text=text,
            metadata={
                "document_type": document_type,
                "method": "pattern_based",
                "field_count": len(
                    extracted_fields
                ),
            },
        )

    # ======================================================
    # EMAIL
    # ======================================================

    def _extract_email(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract email addresses."""

        pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )

        matches = re.findall(
            pattern,
            text,
        )

        matches = list(
            dict.fromkeys(
                match.lower()
                for match in matches
            )
        )

        if not matches:
            return

        fields["email"] = matches[0]

        if len(matches) > 1:
            fields["emails"] = matches

        extracted.append(
            ExtractedField(
                field_name="email",
                value=matches[0],
                confidence=0.98,
            )
        )

    # ======================================================
    # PHONE
    # ======================================================

    def _extract_phone(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract Indian mobile phone numbers."""

        pattern = (
            r"(?<!\d)"
            r"(?:\+91[\s-]?)?"
            r"(?:0[\s-]?)?"
            r"[6-9]\d{4}[\s-]?\d{5}"
            r"(?!\d)"
        )

        matches = re.findall(
            pattern,
            text,
        )

        normalized: list[str] = []

        for match in matches:
            value = re.sub(
                r"\D",
                "",
                match,
            )

            if value.startswith("91") and len(
                value
            ) == 12:
                value = value[-10:]

            elif value.startswith("0") and len(
                value
            ) == 11:
                value = value[-10:]

            if (
                len(value) == 10
                and value[0] in "6789"
                and value not in normalized
            ):
                normalized.append(value)

        if not normalized:
            return

        fields["phone"] = normalized[0]

        if len(normalized) > 1:
            fields["phones"] = normalized

        extracted.append(
            ExtractedField(
                field_name="phone",
                value=normalized[0],
                confidence=0.92,
            )
        )

    # ======================================================
    # PAN
    # ======================================================

    def _extract_pan(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract PAN-like numbers."""

        pattern = (
            r"(?<![A-Z0-9])"
            r"[A-Z]{5}[0-9]{4}[A-Z]"
            r"(?![A-Z0-9])"
        )

        matches = re.findall(
            pattern,
            text.upper(),
        )

        matches = list(
            dict.fromkeys(matches)
        )

        if not matches:
            return

        fields["pan"] = matches[0]

        if len(matches) > 1:
            fields["pans"] = matches

        extracted.append(
            ExtractedField(
                field_name="pan",
                value=matches[0],
                confidence=0.95,
            )
        )

    # ======================================================
    # AADHAAR
    # ======================================================

    def _extract_aadhaar(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract Aadhaar-like 12-digit numbers."""

        pattern = (
            r"(?<!\d)"
            r"(?:\d{4}[\s-]\d{4}[\s-]\d{4}"
            r"|\d{12})"
            r"(?!\d)"
        )

        matches = re.findall(
            pattern,
            text,
        )

        normalized: list[str] = []

        for match in matches:
            value = re.sub(
                r"\D",
                "",
                match,
            )

            if (
                len(value) == 12
                and value not in normalized
            ):
                normalized.append(value)

        if not normalized:
            return

        fields["aadhaar"] = normalized[0]

        if len(normalized) > 1:
            fields["aadhaars"] = normalized

        extracted.append(
            ExtractedField(
                field_name="aadhaar",
                value=normalized[0],
                confidence=0.90,
            )
        )

    # ======================================================
    # DATES
    # ======================================================

    def _extract_dates(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract and validate common date formats."""

        patterns = [
            r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",
            r"\b\d{4}[/-]\d{2}[/-]\d{2}\b",
            (
                r"\b\d{1,2}\s+"
                r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|"
                r"Sep|Oct|Nov|Dec)[a-z]*\s+"
                r"\d{4}\b"
            ),
        ]

        matches: list[str] = []

        for pattern in patterns:
            matches.extend(
                re.findall(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
            )

        valid_dates: list[str] = []

        for value in matches:
            value = value.strip()

            if self._is_valid_date(value):
                if value not in valid_dates:
                    valid_dates.append(value)

        if not valid_dates:
            return

        fields["dates"] = valid_dates

        extracted.append(
            ExtractedField(
                field_name="dates",
                value=", ".join(
                    valid_dates
                ),
                confidence=0.85,
            )
        )

    # ======================================================
    # DATE OF BIRTH
    # ======================================================

    def _extract_date_of_birth(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract a date specifically associated with DOB."""

        pattern = (
            r"(?:date\s+of\s+birth|"
            r"dob|"
            r"birth\s+date)"
            r"\s*[:\-]?\s*"
            r"("
            r"\d{2}[/-]\d{2}[/-]\d{4}"
            r"|"
            r"\d{4}[/-]\d{2}[/-]\d{2}"
            r"|"
            r"\d{1,2}\s+"
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|"
            r"Sep|Oct|Nov|Dec)[a-z]*\s+"
            r"\d{4}"
            r")"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return

        value = match.group(1).strip()

        if not self._is_valid_date(value):
            return

        fields["date_of_birth"] = value

        extracted.append(
            ExtractedField(
                field_name="date_of_birth",
                value=value,
                confidence=0.93,
            )
        )

    # ======================================================
    # ANNUAL INCOME
    # ======================================================

    def _extract_income(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """
        Extract annual/family income.

        Examples:

            Annual Family Income: ₹2,50,000
            Annual Income: 250000
            Family Income - Rs. 2,50,000
            Income: ₹250000
        """

        pattern = (
            r"(?:annual\s+family\s+income|"
            r"annual\s+income|"
            r"family\s+income|"
            r"yearly\s+income|"
            r"total\s+annual\s+income)"
            r"\s*[:\-]?\s*"
            r"(?:₹|rs\.?|inr)?"
            r"\s*"
            r"([0-9][0-9,\s]*)"
        )

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            return

        raw_value = match.group(1).strip()

        numeric_value = re.sub(
            r"[,\s]",
            "",
            raw_value,
        )

        if not numeric_value.isdigit():
            return

        income = int(
            numeric_value
        )

        fields["annual_income"] = income

        extracted.append(
            ExtractedField(
                field_name="annual_income",
                value=str(income),
                confidence=0.90,
            )
        )

    # ======================================================
    # NAMED FIELDS
    # ======================================================

    def _extract_named_fields(
        self,
        text: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract simple labeled fields."""

        labels = {
            "name": [
                "full name",
                "applicant name",
                "candidate name",
                "beneficiary name",
                "name",
            ],
            "father_name": [
                "father's name",
                "father’s name",
                "father name",
                "father",
                "s/o",
                "son of",
            ],
            "mother_name": [
                "mother's name",
                "mother’s name",
                "mother name",
                "mother",
                "m/o",
                "daughter of",
            ],
            "address": [
                "residential address",
                "permanent address",
                "present address",
                "address",
            ],
        }

        for field_name, field_labels in (
            labels.items()
        ):
            value = self._find_labeled_value(
                text,
                field_labels,
            )

            if not value:
                continue

            value = self._clean_field_value(
                value
            )

            if not value:
                continue

            fields[field_name] = value

            confidence = (
                0.82
                if field_name == "name"
                else 0.75
            )

            extracted.append(
                ExtractedField(
                    field_name=field_name,
                    value=value,
                    confidence=confidence,
                )
            )

    # ======================================================
    # DOCUMENT-SPECIFIC FIELDS
    # ======================================================

    def _extract_document_specific_fields(
        self,
        text: str,
        document_type: str,
        fields: dict[str, Any],
        extracted: list[ExtractedField],
    ) -> None:
        """Extract fields useful for specific document types."""

        if document_type == "income_certificate":
            self._extract_labeled_field(
                text,
                "certificate_number",
                [
                    "certificate number",
                    "certificate no",
                    "certificate no.",
                    "cert no",
                    "cert no.",
                ],
                fields,
                extracted,
                confidence=0.88,
            )

        elif document_type == "caste_certificate":
            self._extract_labeled_field(
                text,
                "certificate_number",
                [
                    "certificate number",
                    "certificate no",
                    "certificate no.",
                ],
                fields,
                extracted,
                confidence=0.88,
            )

            self._extract_labeled_field(
                text,
                "caste",
                [
                    "caste",
                    "community",
                    "category",
                ],
                fields,
                extracted,
                confidence=0.80,
            )

        elif document_type == "passport":
            self._extract_labeled_field(
                text,
                "passport_number",
                [
                    "passport number",
                    "passport no",
                    "passport no.",
                ],
                fields,
                extracted,
                confidence=0.90,
            )

        elif document_type == "bank_statement":
            self._extract_labeled_field(
                text,
                "account_number",
                [
                    "account number",
                    "account no",
                    "account no.",
                ],
                fields,
                extracted,
                confidence=0.88,
            )

        elif document_type == "marksheet":
            self._extract_labeled_field(
                text,
                "roll_number",
                [
                    "roll number",
                    "roll no",
                    "roll no.",
                    "registration number",
                    "registration no",
                ],
                fields,
                extracted,
                confidence=0.88,
            )

    # ======================================================
    # LABELED FIELD
    # ======================================================

    def _extract_labeled_field(
        self,
        text: str,
        field_name: str,
        labels: list[str],
        fields: dict[str, Any],
        extracted: list[ExtractedField],
        confidence: float,
    ) -> None:
        """Extract one generic labeled field."""

        value = self._find_labeled_value(
            text,
            labels,
        )

        if not value:
            return

        value = self._clean_field_value(
            value
        )

        if not value:
            return

        if field_name in fields:
            return

        fields[field_name] = value

        extracted.append(
            ExtractedField(
                field_name=field_name,
                value=value,
                confidence=confidence,
            )
        )

    # ======================================================
    # FIND LABELED VALUE
    # ======================================================

    @staticmethod
    def _find_labeled_value(
        text: str,
        labels: list[str],
    ) -> str | None:
        """
        Find a value following a label.

        Handles:

            Name: Sannik Garai
            Name - Sannik Garai
            Name    Sannik Garai
        """

        sorted_labels = sorted(
            labels,
            key=len,
            reverse=True,
        )

        label_pattern = "|".join(
            re.escape(label)
            for label in sorted_labels
        )

        pattern = (
            rf"(?im)^[ \t]*"
            rf"(?:{label_pattern})"
            rf"[ \t]*(?:[:\-]|[ \t])"
            rf"[ \t]*"
            rf"([^\n\r]+)"
        )

        match = re.search(
            pattern,
            text,
        )

        if match:
            return match.group(1).strip()

        # Fallback for labels appearing in the
        # middle of extracted OCR text.
        pattern = (
            rf"(?i)"
            rf"(?:{label_pattern})"
            rf"[ \t]*(?:[:\-])[ \t]*"
            rf"([^\n\r]+)"
        )

        match = re.search(
            pattern,
            text,
        )

        if match:
            return match.group(1).strip()

        return None

    # ======================================================
    # CLEAN FIELD VALUE
    # ======================================================

    @staticmethod
    def _clean_field_value(
        value: str,
    ) -> str:
        """Clean OCR artifacts around extracted values."""

        value = value.strip()

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        value = value.strip(
            " :-–—|"
        )

        return value

    # ======================================================
    # DATE VALIDATION
    # ======================================================

    @staticmethod
    def _is_valid_date(
        value: str,
    ) -> bool:
        """Check whether a detected date is structurally valid."""

        formats = [
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%d/%m/%y",
            "%d-%m-%y",
            "%d %B %Y",
            "%d %b %Y",
        ]

        for date_format in formats:
            try:
                datetime.strptime(
                    value,
                    date_format,
                )
                return True
            except ValueError:
                continue

        return False