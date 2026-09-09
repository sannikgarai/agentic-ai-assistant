"""
Document processing tool.

Handles document analysis operations such as:
- Parsing
- OCR
- Classification
- Information extraction
"""

from __future__ import annotations

from typing import Any


class DocumentTool:
    """Agent tool for document processing."""

    name = "document"

    description = (
        "Process uploaded documents, extract information, "
        "classify documents, and perform OCR."
    )

    def __init__(
        self,
        parser: Any | None = None,
        classifier: Any | None = None,
        extractor: Any | None = None,
        ocr: Any | None = None,
    ):
        self.parser = parser
        self.classifier = classifier
        self.extractor = extractor
        self.ocr = ocr

    async def execute(
        self,
        operation: str,
        file_path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute a document operation."""

        if not isinstance(file_path, str) or not file_path.strip():
            return {
                "success": False,
                "operation": operation,
                "message": "File path is required.",
            }

        if not isinstance(operation, str) or not operation.strip():
            return {
                "success": False,
                "operation": operation,
                "file_path": file_path,
                "message": "Document operation is required.",
            }

        file_path = file_path.strip()
        operation = operation.strip().lower()

        try:
            if operation == "parse":
                result = await self._parse(
                    file_path,
                    **kwargs,
                )

            elif operation == "classify":
                result = await self._classify(
                    file_path,
                    **kwargs,
                )

            elif operation == "extract":
                result = await self._extract(
                    file_path,
                    **kwargs,
                )

            elif operation == "ocr":
                result = await self._ocr(
                    file_path,
                    **kwargs,
                )

            else:
                return {
                    "success": False,
                    "operation": operation,
                    "file_path": file_path,
                    "message": (
                        f"Unsupported document operation: "
                        f"{operation}"
                    ),
                }

            return {
                "success": True,
                "operation": operation,
                "file_path": file_path,
                "result": result,
            }

        except Exception as exc:
            return {
                "success": False,
                "operation": operation,
                "file_path": file_path,
                "error": str(exc),
                "message": "Document processing failed.",
            }

    async def _parse(
        self,
        file_path: str,
        **kwargs: Any,
    ) -> Any:
        if self.parser is None:
            return {
                "status": "not_connected",
                "message": (
                    "Document parser is not connected yet."
                ),
            }

        if hasattr(self.parser, "parse"):
            result = self.parser.parse(
                file_path,
                **kwargs,
            )

            if hasattr(result, "__await__"):
                result = await result

            return result

        raise RuntimeError(
            "Document parser does not provide parse()."
        )

    async def _classify(
        self,
        file_path: str,
        **kwargs: Any,
    ) -> Any:
        if self.classifier is None:
            return {
                "status": "not_connected",
                "message": (
                    "Document classifier is not connected yet."
                ),
            }

        if hasattr(self.classifier, "classify"):
            result = self.classifier.classify(
                file_path,
                **kwargs,
            )

            if hasattr(result, "__await__"):
                result = await result

            return result

        raise RuntimeError(
            "Document classifier does not provide "
            "classify()."
        )

    async def _extract(
        self,
        file_path: str,
        **kwargs: Any,
    ) -> Any:
        if self.extractor is None:
            return {
                "status": "not_connected",
                "message": (
                    "Document extractor is not connected yet."
                ),
            }

        if hasattr(self.extractor, "extract"):
            result = self.extractor.extract(
                file_path,
                **kwargs,
            )

            if hasattr(result, "__await__"):
                result = await result

            return result

        raise RuntimeError(
            "Document extractor does not provide "
            "extract()."
        )

    async def _ocr(
        self,
        file_path: str,
        **kwargs: Any,
    ) -> Any:
        if self.ocr is None:
            return {
                "status": "not_connected",
                "message": (
                    "OCR engine is not connected yet."
                ),
            }

        if hasattr(self.ocr, "process"):
            result = self.ocr.process(
                file_path,
                **kwargs,
            )

            if hasattr(result, "__await__"):
                result = await result

            return result

        if hasattr(self.ocr, "extract_text"):
            result = self.ocr.extract_text(
                file_path,
                **kwargs,
            )

            if hasattr(result, "__await__"):
                result = await result

            return result

        raise RuntimeError(
            "OCR engine does not provide a supported method."
        )