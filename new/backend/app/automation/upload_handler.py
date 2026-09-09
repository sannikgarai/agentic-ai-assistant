"""
File upload handling for automated forms.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class UploadResult:
    """Result of an upload operation."""

    success: bool
    field_name: str
    selector: str
    file_path: str
    message: str
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "field_name": self.field_name,
            "selector": self.selector,
            "file_path": self.file_path,
            "message": self.message,
            "metadata": self.metadata,
        }


class UploadHandler:
    """Upload files through Playwright."""

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }

    async def upload(
        self,
        page,
        field_name: str,
        selector: str,
        file_path: str | Path,
        timeout: int = 10000,
    ) -> UploadResult:
        """Upload a single file."""

        path = Path(file_path)

        if not path.exists():
            return UploadResult(
                success=False,
                field_name=field_name,
                selector=selector,
                file_path=str(path),
                message="File does not exist.",
            )

        if not path.is_file():
            return UploadResult(
                success=False,
                field_name=field_name,
                selector=selector,
                file_path=str(path),
                message="Path is not a file.",
            )

        if (
            path.suffix.lower()
            not in self.ALLOWED_EXTENSIONS
        ):
            return UploadResult(
                success=False,
                field_name=field_name,
                selector=selector,
                file_path=str(path),
                message=(
                    f"Unsupported file type: "
                    f"{path.suffix}"
                ),
            )

        try:
            locator = page.locator(
                selector
            )

            await locator.wait_for(
                state="attached",
                timeout=timeout,
            )

            await locator.set_input_files(
                str(path)
            )

            return UploadResult(
                success=True,
                field_name=field_name,
                selector=selector,
                file_path=str(path),
                message="File uploaded successfully.",
                metadata={
                    "extension": path.suffix.lower(),
                    "size": path.stat().st_size,
                },
            )

        except Exception as exc:
            return UploadResult(
                success=False,
                field_name=field_name,
                selector=selector,
                file_path=str(path),
                message=str(exc),
            )

    async def upload_multiple(
        self,
        page,
        uploads: list[dict[str, Any]],
        timeout: int = 10000,
    ) -> list[UploadResult]:
        """Upload multiple documents."""

        results = []

        for upload in uploads:
            result = await self.upload(
                page=page,
                field_name=upload.get(
                    "field_name",
                    "",
                ),
                selector=upload.get(
                    "selector",
                    "",
                ),
                file_path=upload.get(
                    "file_path",
                    "",
                ),
                timeout=timeout,
            )

            results.append(result)

        return results