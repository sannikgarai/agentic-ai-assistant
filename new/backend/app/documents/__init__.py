"""
Document processing package.

Provides:
- Document parsing
- Document classification
- Structured field extraction
- OCR processing
"""

from .classifier import (
    ClassificationResult,
    DocumentClassifier,
)

from .extractor import (
    DocumentExtractor,
    ExtractedField,
    ExtractionResult,
)

from .ocr import OCREngine

from .parser import (
    DocumentParser,
    ParsedDocument,
    ParsedPage,
)


__all__ = [
    "DocumentParser",
    "ParsedDocument",
    "ParsedPage",
    "DocumentClassifier",
    "ClassificationResult",
    "DocumentExtractor",
    "ExtractedField",
    "ExtractionResult",
    "OCREngine",
]