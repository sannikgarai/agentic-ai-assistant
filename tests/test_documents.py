from pathlib import Path

import pytest


# ==========================================================
# MODULE IMPORT TESTS
# ==========================================================


def test_document_modules_import():
    from app.documents import (
        parser,
        classifier,
        extractor,
        ocr,
    )

    modules = [
        parser,
        classifier,
        extractor,
        ocr,
    ]

    for module in modules:
        assert module is not None


def test_document_parser_imports():
    from app.documents import parser

    assert parser is not None


def test_document_classifier_imports():
    from app.documents import classifier

    assert classifier is not None


def test_document_extractor_imports():
    from app.documents import extractor

    assert extractor is not None


def test_document_ocr_imports():
    from app.documents import ocr

    assert ocr is not None


# ==========================================================
# CONFIGURATION TESTS
# ==========================================================


def test_upload_directory_configured():
    from app.core.config import settings

    directory = Path(
        settings.uploaded_document_dir
    )

    assert directory.name == "uploaded_documents"


def test_processed_directory_configured():
    from app.core.config import settings

    directory = Path(
        settings.processed_document_dir
    )

    assert directory.name == "processed_documents"


def test_max_upload_size_configured():
    from app.core.config import settings

    assert hasattr(
        settings,
        "max_upload_size",
    )

    assert settings.max_upload_size > 0


# ==========================================================
# FILE EXTENSION TESTS
# ==========================================================


def test_pdf_extension():
    filename = "sample.pdf"

    assert Path(
        filename
    ).suffix.lower() == ".pdf"


def test_image_extensions():
    extensions = [
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    ]

    supported = {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    for extension in extensions:
        assert extension in supported


# ==========================================================
# PARSER TESTS
# ==========================================================


def test_document_parser_class_exists():
    from app.documents.parser import (
        DocumentParser,
    )

    parser = DocumentParser()

    assert parser is not None


def test_document_parser_has_parse_method():
    from app.documents.parser import (
        DocumentParser,
    )

    parser = DocumentParser()

    assert hasattr(
        parser,
        "parse",
    )

    assert callable(
        parser.parse
    )


# ==========================================================
# CLASSIFIER TESTS
# ==========================================================


def test_document_classifier_class_exists():
    from app.documents.classifier import (
        DocumentClassifier,
    )

    classifier = DocumentClassifier()

    assert classifier is not None


def test_income_certificate_classification():
    from app.documents.classifier import (
        DocumentClassifier,
    )

    classifier = DocumentClassifier()

    result = classifier.classify(
        text=(
            "This is an Income Certificate. "
            "Annual Income: 150000"
        ),
        filename="income_certificate.pdf",
    )

    assert result.document_type == (
        "income_certificate"
    )

    assert result.confidence > 0


def test_aadhaar_classification():
    from app.documents.classifier import (
        DocumentClassifier,
    )

    classifier = DocumentClassifier()

    result = classifier.classify(
        text=(
            "Unique Identification Authority "
            "of India Aadhaar"
        ),
        filename="aadhaar.pdf",
    )

    assert result.document_type == "aadhaar"

    assert result.confidence > 0


def test_unknown_document_classification():
    from app.documents.classifier import (
        DocumentClassifier,
    )

    classifier = DocumentClassifier()

    result = classifier.classify(
        text="Random document content",
        filename="random.pdf",
    )

    assert result.document_type == "unknown"


# ==========================================================
# EXTRACTOR TESTS
# ==========================================================


def test_document_extractor_class_exists():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    assert extractor is not None


def test_extract_email():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text="Email: test@example.com",
        document_type="unknown",
    )

    assert result.fields.get(
        "email"
    ) == "test@example.com"


def test_extract_phone():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text="Phone: 9876543210",
        document_type="unknown",
    )

    assert result.fields.get(
        "phone"
    ) == "9876543210"


def test_extract_pan():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text="PAN: ABCDE1234F",
        document_type="pan_card",
    )

    assert result.fields.get(
        "pan"
    ) == "ABCDE1234F"


def test_extract_aadhaar():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text="Aadhaar: 1234 5678 9012",
        document_type="aadhaar",
    )

    assert result.fields.get(
        "aadhaar"
    ) == "1234 5678 9012"


def test_extract_income():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text=(
            "Annual Income: ₹150000"
        ),
        document_type="income_certificate",
    )

    assert result.fields.get(
        "annual_income"
    ) == 150000


def test_extract_named_fields():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text=(
            "Name: Sannik Garai\n"
            "Father's Name: Shankar Garai\n"
            "Mother's Name: Kamala Garai"
        ),
        document_type="unknown",
    )

    assert result.fields.get(
        "name"
    ) == "Sannik Garai"

    assert result.fields.get(
        "father_name"
    ) == "Shankar Garai"

    assert result.fields.get(
        "mother_name"
    ) == "Kamala Garai"


def test_empty_document_extraction():
    from app.documents.extractor import (
        DocumentExtractor,
    )

    extractor = DocumentExtractor()

    result = extractor.extract(
        text="",
        document_type="unknown",
    )

    assert result.fields == {}

    assert result.raw_text == ""


# ==========================================================
# OCR TESTS
# ==========================================================


def test_ocr_engine_class_exists():
    from app.documents.ocr import (
        OCREngine,
    )

    engine = OCREngine()

    assert engine is not None


def test_ocr_engine_has_process_method():
    from app.documents.ocr import (
        OCREngine,
    )

    engine = OCREngine()

    assert hasattr(
        engine,
        "process",
    )

    assert callable(
        engine.process
    )


def test_ocr_supported_languages():
    from app.documents.ocr import (
        OCREngine,
    )

    engine = OCREngine()

    assert engine.DEFAULT_LANGUAGES[
        "en"
    ] == "eng"

    assert engine.DEFAULT_LANGUAGES[
        "bn"
    ] == "ben"

    assert engine.DEFAULT_LANGUAGES[
        "hi"
    ] == "hin"

    assert engine.DEFAULT_LANGUAGES[
        "or"
    ] == "ori"

    assert engine.DEFAULT_LANGUAGES[
        "as"
    ] == "asm"


# ==========================================================
# MODULE CONTENT TEST
# ==========================================================


def test_document_module_has_content():
    from app.documents import parser

    public_items = [
        name
        for name in dir(parser)
        if not name.startswith("_")
    ]

    assert len(public_items) > 0