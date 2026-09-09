
"""
RAG package for the Agentic AI Assistant.

Provides the complete Retrieval-Augmented Generation pipeline:
- PDF loading
- Text extraction
- Text cleaning
- Chunking
- Embeddings
- FAISS indexing
- Vector storage
- Retrieval
- Reranking
- End-to-end RAG pipeline
"""

from backend.app.rag.chunker import TextChunk, TextChunker
from backend.app.rag.cleaner import TextCleaner
from backend.app.rag.embeddings import EmbeddingModel
from backend.app.rag.extractor import PDFExtractor
from backend.app.rag.indexing import FAISSIndexer
from backend.app.rag.loader import PDFDocument, PDFLoader
from backend.app.rag.pipeline import RAGPipeline
from backend.app.rag.reranker import Reranker
from backend.app.rag.retriever import Retriever, RetrievalResult
from backend.app.rag.vector_store import VectorStore

__all__ = [
    "PDFDocument",
    "PDFLoader",
    "PDFExtractor",
    "TextCleaner",
    "TextChunk",
    "TextChunker",
    "EmbeddingModel",
    "FAISSIndexer",
    "VectorStore",
    "Retriever",
    "RetrievalResult",
    "Reranker",
    "RAGPipeline",
]
