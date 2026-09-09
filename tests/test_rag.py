from pathlib import Path

import pytest


def test_rag_modules_import():
    from app.rag import (
        loader,
        extractor,
        cleaner,
        chunker,
        embeddings,
        indexing,
        vector_store,
        retriever,
        reranker,
        pipeline,
    )

    modules = [
        loader,
        extractor,
        cleaner,
        chunker,
        embeddings,
        indexing,
        vector_store,
        retriever,
        reranker,
        pipeline,
    ]

    for module in modules:
        assert module is not None


def test_rag_directories_exist():
    from app.core.config import settings

    directories = [
        settings.government_pdf_dir,
        settings.processed_document_dir,
        settings.vector_db_dir,
    ]

    for directory in directories:
        assert isinstance(directory, Path)


def test_rag_configuration_exists():
    from app.core.config import settings

    assert hasattr(settings, "embedding_model")
    assert hasattr(settings, "rag_top_k")
    assert hasattr(settings, "rag_chunk_size")
    assert hasattr(settings, "rag_chunk_overlap")


def test_rag_configuration_values():
    from app.core.config import settings

    assert settings.embedding_model
    assert settings.rag_top_k > 0
    assert settings.rag_chunk_size > 0
    assert settings.rag_chunk_overlap >= 0


def test_chunker_imports():
    from app.rag import chunker

    assert chunker is not None


def test_cleaner_imports():
    from app.rag import cleaner

    assert cleaner is not None


def test_extractor_imports():
    from app.rag import extractor

    assert extractor is not None


def test_embedding_module_imports():
    from app.rag import embeddings

    assert embeddings is not None


def test_vector_store_module_imports():
    from app.rag import vector_store

    assert vector_store is not None


def test_retriever_module_imports():
    from app.rag import retriever

    assert retriever is not None


def test_reranker_module_imports():
    from app.rag import reranker

    assert reranker is not None


def test_pipeline_module_imports():
    from app.rag import pipeline

    assert pipeline is not None


def test_vector_db_path_is_configured():
    from app.core.config import settings

    vector_db_dir = Path(settings.vector_db_dir)

    assert vector_db_dir is not None
    assert vector_db_dir.name == "vector_db"