"""
Document classification.

Classifies documents into useful categories using filename and
text-based heuristics.

The public interface is intentionally simple so that an ML/LLM
classifier can be introduced later without changing callers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClassificationResult:
    """Result of document classification."""

    document_type: str
    confidence: float
    matched_keywords: list[str] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""

        return {
            "document_type": self.document_type,
            "confidence": self.confidence,
            "matched_keywords": self.matched_keywords,
            "metadata": self.metadata,
        }


class DocumentClassifier:
    """Classify government and identity documents."""

    KEYWORDS: dict[str, set[str]] = {
        "aadhaar": {
            "aadhaar",
            "uidai",
            "unique identification",
            "unique identification authority",
        },
        "pan_card": {
            "permanent account number",
            "income tax department",
            "pan card",
            "pan number",
        },
        "voter_id": {
            "election commission",
            "elector",
            "voter",
            "epic",
            "elector photo identity card",
        },
        "driving_license": {
            "driving licence",
            "driving license",
            "transport department",
            "dl number",
            "licence number",
            "license number",
        },
        "passport": {
            "passport",
            "republic of india",
            "passport authority",
        },
        "income_certificate": {
            "income certificate",
            "annual income",
            "income proof",
            "family income",
            "income from all sources",
        },
        "caste_certificate": {
            "caste certificate",
            "scheduled caste",
            "scheduled tribe",
            "other backward class",
            "social category",
            "backward class",
        },
        "residence_certificate": {
            "residence certificate",
            "domicile certificate",
            "residential certificate",
            "proof of residence",
            "permanent resident",
        },
        "birth_certificate": {
            "birth certificate",
            "date of birth",
            "place of birth",
            "registration of birth",
        },
        "death_certificate": {
            "death certificate",
            "date of death",
            "place of death",
            "registration of death",
        },
        "marksheet": {
            "marksheet",
            "mark sheet",
            "marks obtained",
            "grade",
            "semester",
            "academic year",
            "examination",
        },
        "bank_statement": {
            "bank statement",
            "account number",
            "transaction date",
            "transaction history",
            "account balance",
            "opening balance",
            "closing balance",
        },
        "ration_card": {
            "ration card",
            "food and supplies",
            "fair price shop",
            "public distribution system",
            "pds",
        },
        "pension_document": {
            "pension",
            "pensioner",
            "pension scheme",
            "pension payment",
            "pension order",
        },
        "scholarship_document": {
            "scholarship",
            "scholarship scheme",
            "educational assistance",
            "student scholarship",
            "financial assistance for education",
        },
    }

    # Keywords that should be matched as complete words.
    WORD_BOUNDARY_KEYWORDS = {
        "pan",
        "voter",
        "epic",
        "grade",
        "pension",
        "scholarship",
        "elector",
    }

    def classify(
        self,
        text: str = "",
        filename: str = "",
    ) -> ClassificationResult:
        """
        Classify a document using filename and text.

        Filename matches receive slightly more weight because
        filenames such as 'income_certificate.pdf' are useful
        classification signals.
        """

        text = text or ""
        filename = filename or ""

        normalized_text = self._normalize(
            text
        )
        normalized_filename = self._normalize(
            filename
        )

        scores: dict[
            str,
            tuple[float, list[str]],
        ] = {}

        for document_type, keywords in (
            self.KEYWORDS.items()
        ):
            matched_keywords: list[str] = []
            score = 0.0

            for keyword in keywords:
                normalized_keyword = self._normalize(
                    keyword
                )

                filename_match = (
                    self._keyword_matches(
                        normalized_filename,
                        normalized_keyword,
                    )
                )

                text_match = (
                    self._keyword_matches(
                        normalized_text,
                        normalized_keyword,
                    )
                )

                if filename_match:
                    score += 2.0

                    if keyword not in matched_keywords:
                        matched_keywords.append(
                            keyword
                        )

                elif text_match:
                    score += 1.0

                    if keyword not in matched_keywords:
                        matched_keywords.append(
                            keyword
                        )

            if matched_keywords:
                scores[document_type] = (
                    score,
                    matched_keywords,
                )

        if not scores:
            return ClassificationResult(
                document_type="unknown",
                confidence=0.0,
                matched_keywords=[],
                metadata={
                    "method": "keyword_heuristic",
                    "reason": "no_matching_keywords",
                },
            )

        ranked = sorted(
            scores.items(),
            key=lambda item: item[1][0],
            reverse=True,
        )

        best_type, (
            best_score,
            matched_keywords,
        ) = ranked[0]

        second_score = (
            ranked[1][1][0]
            if len(ranked) > 1
            else 0.0
        )

        confidence = self._calculate_confidence(
            best_score=best_score,
            second_score=second_score,
            keyword_count=len(
                self.KEYWORDS[best_type]
            ),
        )

        ambiguous = (
            second_score > 0
            and abs(
                best_score - second_score
            )
            <= 1.0
        )

        if ambiguous:
            confidence *= 0.75

        return ClassificationResult(
            document_type=best_type,
            confidence=round(
                min(confidence, 0.95),
                4,
            ),
            matched_keywords=sorted(
                matched_keywords
            ),
            metadata={
                "method": "keyword_heuristic",
                "score": best_score,
                "second_best_score": second_score,
                "ambiguous": ambiguous,
                "filename_used": bool(
                    normalized_filename
                ),
            },
        )

    # ======================================================
    # NORMALIZATION
    # ======================================================

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """Normalize text for reliable matching."""

        value = value.lower()

        value = re.sub(
            r"[_\-]+",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # ======================================================
    # KEYWORD MATCHING
    # ======================================================

    def _keyword_matches(
        self,
        text: str,
        keyword: str,
    ) -> bool:
        """
        Match a keyword safely.

        Single-word keywords use word boundaries to avoid
        false matches such as 'pan' inside 'company'.
        """

        if not text or not keyword:
            return False

        if keyword in self.WORD_BOUNDARY_KEYWORDS:
            pattern = (
                rf"\b{re.escape(keyword)}\b"
            )

            return bool(
                re.search(
                    pattern,
                    text,
                )
            )

        # Multi-word phrases and longer keywords can
        # safely use normalized substring matching.
        if " " in keyword:
            return keyword in text

        pattern = (
            rf"\b{re.escape(keyword)}\b"
        )

        return bool(
            re.search(
                pattern,
                text,
            )
        )

    # ======================================================
    # CONFIDENCE
    # ======================================================

    @staticmethod
    def _calculate_confidence(
        best_score: float,
        second_score: float,
        keyword_count: int,
    ) -> float:
        """
        Calculate heuristic confidence.

        This is not a statistical probability. It represents
        the strength of the keyword evidence.
        """

        if best_score <= 0:
            return 0.0

        max_possible_score = max(
            keyword_count * 1.25,
            1.0,
        )

        base_confidence = (
            best_score
            / max_possible_score
        )

        if second_score > 0:
            separation = (
                best_score
                - second_score
            ) / max(
                best_score,
                1.0,
            )

            base_confidence *= (
                0.75 + 0.25 * separation
            )

        return max(
            0.0,
            min(
                base_confidence,
                0.95,
            ),
        )

    # ======================================================
    # CONVENIENCE METHODS
    # ======================================================

    def get_supported_types(
        self,
    ) -> list[str]:
        """Return supported document categories."""

        return sorted(
            self.KEYWORDS.keys()
        )

    def is_supported_type(
        self,
        document_type: str,
    ) -> bool:
        """Check whether a document category is supported."""

        return (
            document_type
            in self.KEYWORDS
        )