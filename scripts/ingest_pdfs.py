"""
scripts/ingest_pdfs.py

Ingest government PDFs into the local FAISS vector database.

Project structure expected:

agentic-ai-assistant/
├── backend/
├── data/
│   └── government_pdfs/
├── vector_db/
└── scripts/
    └── ingest_pdfs.py

Run from project root:

    python scripts/ingest_pdfs.py

Optional:

    python scripts/ingest_pdfs.py --clear
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
from pathlib import Path
from typing import Any

import fitz
import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss
except ImportError:
    faiss = None


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("ingest_pdfs")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Basic text normalization.
    """

    if not text:
        return ""

    lines = []

    for line in text.splitlines():
        line = " ".join(line.split())

        if line:
            lines.append(line)

    return "\n".join(lines)


def chunk_text(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.
    """

    words = text.split()

    if not words:
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    chunks: list[str] = []

    step = chunk_size - chunk_overlap

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]

        if not chunk_words:
            break

        chunks.append(" ".join(chunk_words))

        if start + chunk_size >= len(words):
            break

    return chunks


def get_document_type(pdf_path: Path) -> str:
    """
    Determine the document category from the directory name.
    """

    government_root = Path(settings.government_pdf_dir)

    try:
        relative = pdf_path.relative_to(government_root)

        if len(relative.parts) > 1:
            return relative.parts[0]

    except ValueError:
        pass

    return "other"


def extract_pdf_pages(pdf_path: Path) -> list[dict[str, Any]]:
    """
    Extract text page-by-page from a PDF.
    """

    pages: list[dict[str, Any]] = []

    try:
        document = fitz.open(pdf_path)

        with document:
            for page_number, page in enumerate(document, start=1):

                text = page.get_text("text")

                text = clean_text(text)

                if not text:
                    continue

                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )

    except Exception as exc:
        logger.exception(
            "Failed to read PDF: %s | %s",
            pdf_path,
            exc,
        )

    return pages


def collect_pdf_chunks(
    pdf_path: Path,
    chunk_size: int,
    chunk_overlap: int,
) -> list[dict[str, Any]]:
    """
    Extract and chunk one PDF.
    """

    pages = extract_pdf_pages(pdf_path)

    chunks: list[dict[str, Any]] = []

    for page_data in pages:

        page_number = page_data["page"]
        page_text = page_data["text"]

        page_chunks = chunk_text(
            page_text,
            chunk_size,
            chunk_overlap,
        )

        for chunk_number, chunk in enumerate(
            page_chunks,
            start=1,
        ):
            chunks.append(
                {
                    "text": chunk,
                    "source": str(
                        pdf_path.relative_to(PROJECT_ROOT)
                    ),
                    "file_name": pdf_path.name,
                    "document_type": get_document_type(pdf_path),
                    "page": page_number,
                    "chunk": chunk_number,
                }
            )

    return chunks


def load_embedding_model() -> SentenceTransformer:
    """
    Load the configured sentence-transformer model.
    """

    model_name = settings.embedding_model

    logger.info(
        "Loading embedding model: %s",
        model_name,
    )

    return SentenceTransformer(model_name)


def build_faiss_index(
    embeddings: np.ndarray,
) -> Any:
    """
    Create a FAISS cosine-similarity index.

    Embeddings are normalized, so inner product is equivalent
    to cosine similarity.
    """

    if faiss is None:
        raise RuntimeError(
            "FAISS is not installed. Install it with:\n"
            "pip install faiss-cpu"
        )

    embeddings = embeddings.astype("float32")

    faiss.normalize_L2(embeddings)

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)

    return index


def save_index(
    index: Any,
    metadata: list[dict[str, Any]],
) -> None:
    """
    Save FAISS index and metadata.
    """

    vector_dir = Path(settings.vector_db_dir)

    vector_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    index_path = vector_dir / "index.faiss"
    metadata_path = vector_dir / "metadata.json"

    logger.info(
        "Saving FAISS index: %s",
        index_path,
    )

    faiss.write_index(
        index,
        str(index_path),
    )

    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metadata,
            file,
            ensure_ascii=False,
            indent=2,
        )

    logger.info(
        "Saved %d metadata records.",
        len(metadata),
    )


def clear_vector_database() -> None:
    """
    Remove existing vector database files.
    """

    vector_dir = Path(settings.vector_db_dir)

    if vector_dir.exists():

        logger.warning(
            "Clearing vector database: %s",
            vector_dir,
        )

        for item in vector_dir.iterdir():

            if item.is_dir():
                shutil.rmtree(item)

            else:
                item.unlink()

    vector_dir.mkdir(
        parents=True,
        exist_ok=True,
    )


def ingest(
    clear_existing: bool = False,
) -> None:
    """
    Main ingestion pipeline.
    """

    government_pdf_dir = Path(
        settings.government_pdf_dir
    )

    if not government_pdf_dir.exists():

        raise FileNotFoundError(
            f"Government PDF directory does not exist: "
            f"{government_pdf_dir}"
        )

    if clear_existing:
        clear_vector_database()

    pdf_files = sorted(
        government_pdf_dir.rglob("*.pdf")
    )

    if not pdf_files:

        logger.warning(
            "No PDF files found in %s",
            government_pdf_dir,
        )

        return

    logger.info(
        "Found %d PDF files.",
        len(pdf_files),
    )

    chunk_size = int(settings.rag_chunk_size)
    chunk_overlap = int(settings.rag_chunk_overlap)

    all_chunks: list[dict[str, Any]] = []

    for pdf_number, pdf_path in enumerate(
        pdf_files,
        start=1,
    ):

        logger.info(
            "[%d/%d] Processing %s",
            pdf_number,
            len(pdf_files),
            pdf_path.name,
        )

        chunks = collect_pdf_chunks(
            pdf_path,
            chunk_size,
            chunk_overlap,
        )

        all_chunks.extend(chunks)

        logger.info(
            "Created %d chunks from %s",
            len(chunks),
            pdf_path.name,
        )

    if not all_chunks:

        logger.warning(
            "No text chunks were generated."
        )

        return

    logger.info(
        "Total chunks: %d",
        len(all_chunks),
    )

    texts = [
        item["text"]
        for item in all_chunks
    ]

    model = load_embedding_model()

    logger.info(
        "Generating embeddings..."
    )

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        convert_to_numpy=True,
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32",
    )

    logger.info(
        "Embedding shape: %s",
        embeddings.shape,
    )

    index = build_faiss_index(
        embeddings
    )

    save_index(
        index,
        all_chunks,
    )

    logger.info(
        "PDF ingestion completed successfully."
    )


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Ingest government PDFs into FAISS."
        )
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help=(
            "Delete the existing vector database "
            "before ingestion."
        ),
    )

    args = parser.parse_args()

    ingest(
        clear_existing=args.clear
    )


if __name__ == "__main__":
    main()