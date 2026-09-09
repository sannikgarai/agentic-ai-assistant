"""
scripts/rebuild_index.py

Completely rebuild the FAISS vector database from
government PDFs.

Run from project root:

    python scripts/rebuild_index.py
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# Import the ingestion pipeline
from scripts.ingest_pdfs import ingest


def main() -> None:
    """
    Delete the existing vector database and rebuild it
    from all government PDFs.
    """

    print()
    print("=" * 70)
    print("       REBUILDING GOVERNMENT PDF VECTOR DATABASE")
    print("=" * 70)
    print()

    try:

        ingest(
            clear_existing=True
        )

        print()
        print("=" * 70)
        print("              VECTOR DATABASE REBUILT")
        print("=" * 70)
        print()

    except Exception as exc:

        print()
        print("=" * 70)
        print("              REBUILD FAILED")
        print("=" * 70)
        print()

        print(f"Error: {exc}")

        raise


if __name__ == "__main__":
    main()