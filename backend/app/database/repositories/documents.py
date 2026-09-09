
"""
Document repository.
"""

from __future__ import annotations

from typing import Any

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)


class DocumentRepository:
    """Database operations for uploaded documents."""

    TABLE = "documents"

    def __init__(
        self,
        database: SupabaseDatabase | None = None,
    ):
        self.database = database or get_database()

    def create(
        self,
        user_id: str,
        file_name: str,
        file_path: str,
        document_type: str = "unknown",
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a document record."""

        if not user_id:
            raise ValueError("user_id is required.")

        if not file_name:
            raise ValueError("file_name is required.")

        if not file_path:
            raise ValueError("file_path is required.")

        payload: dict[str, Any] = {
            "user_id": user_id,
            "file_name": file_name,
            "file_path": file_path,
            "document_type": document_type,
        }

        if mime_type is not None:
            payload["mime_type"] = mime_type

        if metadata is not None:
            payload["metadata"] = metadata

        response = (
            self.database
            .table(self.TABLE)
            .insert(payload)
            .execute()
        )

        if not response.data:
            raise RuntimeError(
                "Failed to create document record."
            )

        return response.data[0]

    def get(
        self,
        document_id: str,
    ) -> dict[str, Any] | None:
        """Get document metadata."""

        if not document_id:
            raise ValueError(
                "document_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("id", document_id)
            .limit(1)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def list_for_user(
        self,
        user_id: str,
        document_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List user documents."""

        if not user_id:
            raise ValueError(
                "user_id is required."
            )

        if limit < 1:
            raise ValueError(
                "limit must be greater than 0."
            )

        query = (
            self.database
            .table(self.TABLE)
            .select("*")
            .eq("user_id", user_id)
        )

        if document_type:
            query = query.eq(
                "document_type",
                document_type,
            )

        response = (
            query
            .order(
                "created_at",
                desc=True,
            )
            .limit(limit)
            .execute()
        )

        return response.data or []

    def update(
        self,
        document_id: str,
        data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Update document metadata."""

        if not document_id:
            raise ValueError(
                "document_id is required."
            )

        if not data:
            raise ValueError(
                "Update data cannot be empty."
            )

        response = (
            self.database
            .table(self.TABLE)
            .update(data)
            .eq("id", document_id)
            .execute()
        )

        return (
            response.data[0]
            if response.data
            else None
        )

    def delete(
        self,
        document_id: str,
    ) -> bool:
        """Delete document record."""

        if not document_id:
            raise ValueError(
                "document_id is required."
            )

        response = (
            self.database
            .table(self.TABLE)
            .delete()
            .eq("id", document_id)
            .execute()
        )

        return bool(response.data)
