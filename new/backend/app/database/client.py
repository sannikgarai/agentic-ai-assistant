
"""
Supabase database client.

Provides a single database abstraction used by repository classes.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from supabase import Client, create_client

from backend.app.core.config import settings


class SupabaseDatabase:
    """Central Supabase database client."""

    def __init__(
        self,
        url: str | None = None,
        key: str | None = None,
    ):
        self.url = url or settings.supabase_url
        self.key = key or settings.supabase_service_role_key

        if not self.url:
            raise ValueError(
                "SUPABASE_URL is not configured."
            )

        if not self.key:
            raise ValueError(
                "SUPABASE_SERVICE_ROLE_KEY is not configured."
            )

        self.client: Client = create_client(
            self.url,
            self.key,
        )

    def table(
        self,
        table_name: str,
    ):
        """Return a Supabase table query."""

        if not table_name:
            raise ValueError(
                "Table name cannot be empty."
            )

        return self.client.table(table_name)

    def health_check(self) -> bool:
        """
        Perform a lightweight database health check.

        Returns:
            True if the profiles table can be queried,
            otherwise False.
        """

        try:
            self.client.table(
                "profiles"
            ).select(
                "id"
            ).limit(1).execute()

            return True

        except Exception:
            return False

    def execute(
        self,
        query,
    ) -> Any:
        """Execute a prepared Supabase query."""

        return query.execute()


@lru_cache(maxsize=1)
def get_database() -> SupabaseDatabase:
    """
    Return the shared database instance.

    The database client is created only once and reused.
    """

    return SupabaseDatabase()
