
"""
scripts/test_pipeline.py

Test the local RAG pipeline and Agent end-to-end workflow.

Run from project root:

    python scripts/test_pipeline.py

Optional query:

    python scripts/test_pipeline.py --query "scholarship eligibility"

This test checks:

1. Configuration
2. Required directories
3. Government PDFs
4. FAISS vector database
5. Embedding model
6. Direct RAG retrieval
7. Agent initialization
8. Agent -> Task Decomposer -> Planner -> Workflow -> RAG -> Gemini
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

try:
    import faiss
except ImportError:
    faiss = None


# ---------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------

from backend.app.agent.agent import Agent
from backend.app.core.config import (
    GOVERNMENT_PDF_DIR,
    PROCESSED_DOCUMENT_DIR,
    UPLOADED_DOCUMENT_DIR,
    VECTOR_DB_DIR,
    settings,
)


# ---------------------------------------------------------------------
# Test result
# ---------------------------------------------------------------------

class TestResult:
    """Simple test result tracker."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def success(self, message: str) -> None:
        self.passed += 1
        print(f"[PASS] {message}")

    def failure(self, message: str) -> None:
        self.failed += 1
        print(f"[FAIL] {message}")

    def summary(self) -> None:
        total = self.passed + self.failed

        print()
        print("=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total : {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        if self.failed == 0:
            print()
            print("All tests passed.")
        else:
            print()
            print("Some tests failed.")

        print("=" * 70)


# ---------------------------------------------------------------------
# Configuration test
# ---------------------------------------------------------------------

def test_configuration(result: TestResult) -> None:
    required_settings = [
        ("embedding_model", settings.embedding_model),
        ("rag_top_k", settings.rag_top_k),
        ("rag_chunk_size", settings.rag_chunk_size),
        ("rag_chunk_overlap", settings.rag_chunk_overlap),
    ]

    for name, value in required_settings:
        if value is not None:
            result.success(
                f"Configuration '{name}' is set."
            )
        else:
            result.failure(
                f"Configuration '{name}' is missing."
            )


# ---------------------------------------------------------------------
# Path tests
# ---------------------------------------------------------------------

def test_directories(result: TestResult) -> None:
    directories = {
        "Government PDFs": Path(
            GOVERNMENT_PDF_DIR
        ),
        "Uploaded documents": Path(
            UPLOADED_DOCUMENT_DIR
        ),
        "Processed documents": Path(
            PROCESSED_DOCUMENT_DIR
        ),
        "Vector database": Path(
            VECTOR_DB_DIR
        ),
    }

    for name, path in directories.items():
        if path.exists():
            result.success(
                f"{name}: {path}"
            )
        else:
            result.failure(
                f"{name} missing: {path}"
            )


# ---------------------------------------------------------------------
# PDF test
# ---------------------------------------------------------------------

def test_pdfs(result: TestResult) -> None:
    pdf_dir = Path(
        GOVERNMENT_PDF_DIR
    )

    if not pdf_dir.exists():
        result.failure(
            f"Government PDF directory missing: {pdf_dir}"
        )
        return

    pdf_files = list(
        pdf_dir.rglob("*.pdf")
    )

    if pdf_files:
        result.success(
            f"Found {len(pdf_files)} government PDF(s)."
        )
    else:
        result.failure(
            "No government PDFs found."
        )


# ---------------------------------------------------------------------
# FAISS test
# ---------------------------------------------------------------------

def test_vector_database(
    result: TestResult,
) -> tuple[object | None, list[dict]]:
    """Load FAISS index and metadata."""

    if faiss is None:
        result.failure(
            "faiss-cpu is not installed."
        )
        return None, []

    vector_dir = Path(
        VECTOR_DB_DIR
    )

    index_path = vector_dir / "index.faiss"
    metadata_path = vector_dir / "metadata.json"

    if not index_path.exists():
        result.failure(
            f"FAISS index missing: {index_path}"
        )
        return None, []

    result.success(
        "FAISS index file exists."
    )

    if not metadata_path.exists():
        result.failure(
            f"Metadata file missing: {metadata_path}"
        )
        return None, []

    result.success(
        "Metadata file exists."
    )

    try:
        index = faiss.read_index(
            str(index_path)
        )

        result.success(
            f"FAISS index loaded. "
            f"Vectors: {index.ntotal}"
        )

    except Exception as exc:
        result.failure(
            f"Unable to load FAISS index: {exc}"
        )
        return None, []

    try:
        with metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        if not isinstance(metadata, list):
            result.failure(
                "metadata.json is not a list."
            )
            return index, []

        if len(metadata) != index.ntotal:
            result.failure(
                "FAISS vector count and metadata "
                "count do not match."
            )
        else:
            result.success(
                "FAISS vectors and metadata count match."
            )

        return index, metadata

    except Exception as exc:
        result.failure(
            f"Unable to load metadata: {exc}"
        )
        return index, []


# ---------------------------------------------------------------------
# Embedding test
# ---------------------------------------------------------------------

def test_embedding_model(
    result: TestResult,
) -> SentenceTransformer | None:
    try:
        model_name = settings.embedding_model

        print(
            f"Loading embedding model: {model_name}"
        )

        model = SentenceTransformer(
            model_name
        )

        test_text = (
            "Government scholarship eligibility"
        )

        embedding = model.encode(
            [test_text],
            convert_to_numpy=True,
        )

        embedding = np.asarray(
            embedding
        )

        if embedding.ndim != 2:
            result.failure(
                "Embedding has unexpected shape."
            )
            return None

        result.success(
            f"Embedding model works. "
            f"Shape: {embedding.shape}"
        )

        return model

    except Exception as exc:
        result.failure(
            f"Embedding model failed: {exc}"
        )
        return None


# ---------------------------------------------------------------------
# Retrieval test
# ---------------------------------------------------------------------

def test_retrieval(
    result: TestResult,
    index,
    metadata: list[dict],
    model: SentenceTransformer | None,
    query: str,
) -> None:
    if index is None:
        result.failure(
            "Retrieval skipped because FAISS index "
            "could not be loaded."
        )
        return

    if model is None:
        result.failure(
            "Retrieval skipped because embedding "
            "model could not be loaded."
        )
        return

    if not metadata:
        result.failure(
            "Retrieval skipped because metadata is empty."
        )
        return

    try:
        query_embedding = model.encode(
            [query],
            convert_to_numpy=True,
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        if faiss is not None:
            faiss.normalize_L2(
                query_embedding
            )

        top_k = min(
            int(settings.rag_top_k),
            index.ntotal,
        )

        scores, indices = index.search(
            query_embedding,
            top_k,
        )

        print()
        print("=" * 70)
        print("RETRIEVAL TEST")
        print("=" * 70)
        print(f"Query: {query}")
        print()

        found = False

        for rank, (
            score,
            vector_index,
        ) in enumerate(
            zip(
                scores[0],
                indices[0],
            ),
            start=1,
        ):
            if vector_index < 0:
                continue

            if vector_index >= len(metadata):
                continue

            item = metadata[
                int(vector_index)
            ]

            found = True

            print(f"Result #{rank}")

            print(
                f"Score : {float(score):.4f}"
            )

            print(
                f"Source: "
                f"{item.get('source', 'unknown')}"
            )

            print(
                f"Page  : "
                f"{item.get(
                    'page',
                    item.get(
                        'page_number',
                        'unknown',
                    ),
                )}"
            )

            text = item.get(
                "text",
                "",
            )

            preview = (
                text[:300]
                + ("..." if len(text) > 300 else "")
            )

            print(
                f"Text  : {preview}"
            )

            print("-" * 70)

        if found:
            result.success(
                "RAG retrieval returned results."
            )
        else:
            result.failure(
                "RAG retrieval returned no results."
            )

    except Exception as exc:
        result.failure(
            f"Retrieval failed: {exc}"
        )


# ---------------------------------------------------------------------
# Agent end-to-end test
# ---------------------------------------------------------------------

async def test_agent(
    result: TestResult,
    query: str,
) -> None:
    """
    Test the complete Agent workflow.

    Agent flow:

        User request
            ↓
        Task Decomposer
            ↓
        Planner
            ↓
        Workflow
            ↓
        RAG Tool
            ↓
        Gemini
            ↓
        Final response
    """

    print()
    print("=" * 70)
    print("AGENT END-TO-END TEST")
    print("=" * 70)
    print(f"Query: {query}")
    print()

    # -------------------------------------------------------------
    # Agent initialization
    # -------------------------------------------------------------

    try:
        print("Creating Agent...")

        agent = Agent()

        result.success(
            "Agent initialized successfully."
        )

    except Exception as exc:
        result.failure(
            "Agent initialization failed: "
            f"{type(exc).__name__}: {exc}"
        )
        return

    # -------------------------------------------------------------
    # Agent execution
    # -------------------------------------------------------------

    try:
        print("Running Agent...")
        print()

        agent_result = await agent.run(
            user_id="test-user",
            message=query,
            language="en",
        )

        print()
        print("-" * 70)
        print("AGENT RESULT")
        print("-" * 70)

        print(
            f"Success : {agent_result.success}"
        )

        print(
            f"Status  : {agent_result.status}"
        )

        print(
            f"Tasks   : "
            f"{len(agent_result.state.tasks)}"
        )

        print(
            f"Retrieved: "
            f"{len(agent_result.state.retrieved_context)}"
        )

        print()
        print("Response:")
        print(agent_result.response)

        print("-" * 70)

        # ---------------------------------------------------------
        # Success check
        # ---------------------------------------------------------

        if agent_result.success:
            result.success(
                "Agent workflow completed successfully."
            )
        else:
            result.failure(
                "Agent workflow returned unsuccessful result."
            )

        # ---------------------------------------------------------
        # Task check
        # ---------------------------------------------------------

        if agent_result.state.tasks:
            result.success(
                f"Agent created "
                f"{len(agent_result.state.tasks)} task(s)."
            )
        else:
            result.failure(
                "Agent created no tasks."
            )

        # ---------------------------------------------------------
        # RAG context check
        # ---------------------------------------------------------

        if agent_result.state.retrieved_context:
            result.success(
                "Agent retrieved context from RAG."
            )
        else:
            print(
                "[INFO] Agent did not return retrieved context."
            )

        # ---------------------------------------------------------
        # Final response check
        # ---------------------------------------------------------

        if agent_result.response.strip():
            result.success(
                "Agent generated a final response."
            )
        else:
            result.failure(
                "Agent returned an empty final response."
            )

    except Exception as exc:
        result.failure(
            "Agent execution failed: "
            f"{type(exc).__name__}: {exc}"
        )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Test Agentic AI Assistant "
            "RAG pipeline and Agent workflow."
        )
    )

    parser.add_argument(
        "--query",
        type=str,
        default=(
            "What government scholarship "
            "information is available in "
            "the indexed documents?"
        ),
        help="Query used for RAG and Agent testing.",
    )

    args = parser.parse_args()

    print()
    print("=" * 70)
    print(
        "       AGENTIC AI ASSISTANT - PIPELINE TEST"
    )
    print("=" * 70)
    print()

    test_result = TestResult()

    # -------------------------------------------------------------
    # 1. Configuration
    # -------------------------------------------------------------

    print()
    print("1. Configuration")
    print("-" * 70)

    test_configuration(
        test_result
    )

    # -------------------------------------------------------------
    # 2. Directories
    # -------------------------------------------------------------

    print()
    print("2. Directories")
    print("-" * 70)

    test_directories(
        test_result
    )

    # -------------------------------------------------------------
    # 3. Government PDFs
    # -------------------------------------------------------------

    print()
    print("3. Government PDFs")
    print("-" * 70)

    test_pdfs(
        test_result
    )

    # -------------------------------------------------------------
    # 4. Vector database
    # -------------------------------------------------------------

    print()
    print("4. Vector Database")
    print("-" * 70)

    index, metadata = test_vector_database(
        test_result
    )

    # -------------------------------------------------------------
    # 5. Embedding model
    # -------------------------------------------------------------

    print()
    print("5. Embedding Model")
    print("-" * 70)

    model = test_embedding_model(
        test_result
    )

    # -------------------------------------------------------------
    # 6. Direct RAG retrieval
    # -------------------------------------------------------------

    print()
    print("6. Direct RAG Retrieval")
    print("-" * 70)

    test_retrieval(
        test_result,
        index,
        metadata,
        model,
        args.query,
    )

    # -------------------------------------------------------------
    # 7. Full Agent workflow
    # -------------------------------------------------------------

    print()
    print("7. Agent End-to-End Workflow")
    print("-" * 70)

    asyncio.run(
        test_agent(
            test_result,
            args.query,
        )
    )

    # -------------------------------------------------------------
    # Final summary
    # -------------------------------------------------------------

    test_result.summary()

    if test_result.failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
