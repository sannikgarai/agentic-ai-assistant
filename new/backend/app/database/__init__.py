"""
Database package.

Provides the Supabase database client and repository layer.
"""

from backend.app.database.client import (
    SupabaseDatabase,
    get_database,
)

__all__ = [
    "SupabaseDatabase",
    "get_database",
]
