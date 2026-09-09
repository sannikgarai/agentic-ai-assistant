"""
backend/app/core/config.py

Application configuration and environment settings.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[3]

BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BASE_DIR / "data"

GOVERNMENT_PDF_DIR = DATA_DIR / "government_pdfs"
UPLOADED_DOCUMENT_DIR = DATA_DIR / "uploaded_documents"
PROCESSED_DOCUMENT_DIR = DATA_DIR / "processed_documents"
AUDIO_DIR = DATA_DIR / "audio"
TEMP_DIR = DATA_DIR / "temp"

VECTOR_DB_DIR = BASE_DIR / "vector_db"


# ---------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Central application configuration.

    Values can be supplied through environment variables
    or backend/.env.
    """

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -----------------------------------------------------------------
    # Application
    # -----------------------------------------------------------------

    app_name: str = Field(
        default="Agentic AI Assistant",
        validation_alias="APP_NAME",
    )

    app_version: str = Field(
        default="1.0.0",
        validation_alias="APP_VERSION",
    )

    environment: str = Field(
        default="development",
        validation_alias="ENVIRONMENT",
    )

    debug: bool = Field(
        default=True,
        validation_alias="DEBUG",
    )

    api_prefix: str = Field(
        default="/api",
        validation_alias="API_PREFIX",
    )

    # -----------------------------------------------------------------
    # Server
    # -----------------------------------------------------------------

    host: str = Field(
        default="127.0.0.1",
        validation_alias="HOST",
    )

    port: int = Field(
        default=8000,
        validation_alias="PORT",
    )

    # -----------------------------------------------------------------
    # Frontend / CORS
    # -----------------------------------------------------------------

    frontend_url: str = Field(
        default="http://localhost:5173",
        validation_alias="FRONTEND_URL",
    )

    allowed_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        validation_alias="ALLOWED_ORIGINS",
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value):
        """
        Support either JSON-style or comma-separated origins.
        """

        if value is None:
            return [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
            ]

        if isinstance(value, str):
            value = value.strip()

            if not value:
                return [
                    "http://localhost:5173",
                    "http://127.0.0.1:5173",
                ]

            # Support comma-separated values in .env
            if "," in value:
                return [
                    origin.strip()
                    for origin in value.split(",")
                    if origin.strip()
                ]

            return [value]

        return value

    # -----------------------------------------------------------------
    # Gemini
    # -----------------------------------------------------------------

    gemini_api_key: str = Field(
        default="",
        validation_alias="GEMINI_API_KEY",
    )

    gemini_model: str = Field(
        default="gemini-3.6-flash",
        validation_alias="GEMINI_MODEL",
    )

    # -----------------------------------------------------------------
    # Supabase
    # -----------------------------------------------------------------

    supabase_url: str = Field(
        default="",
        validation_alias="SUPABASE_URL",
    )

    supabase_anon_key: str = Field(
        default="",
        validation_alias="SUPABASE_ANON_KEY",
    )

    supabase_service_role_key: str = Field(
        default="",
        validation_alias="SUPABASE_SERVICE_ROLE_KEY",
    )

    # -----------------------------------------------------------------
    # RAG
    # -----------------------------------------------------------------

    government_pdf_dir: str = Field(
        default=str(GOVERNMENT_PDF_DIR),
        validation_alias="GOVERNMENT_PDF_DIR",
    )

    vector_db_dir: str = Field(
        default=str(VECTOR_DB_DIR),
        validation_alias="VECTOR_DB_DIR",
    )

    embedding_model: str = Field(
        default=(
            "sentence-transformers/"
            "all-MiniLM-L6-v2"
        ),
        validation_alias="EMBEDDING_MODEL",
    )

    vector_db_path: str = Field(
        default=str(VECTOR_DB_DIR),
        validation_alias="VECTOR_DB_PATH",
    )

    rag_top_k: int = Field(
        default=5,
        validation_alias="RAG_TOP_K",
    )

    rag_chunk_size: int = Field(
        default=500,
        validation_alias="RAG_CHUNK_SIZE",
    )

    rag_chunk_overlap: int = Field(
        default=50,
        validation_alias="RAG_CHUNK_OVERLAP",
    )

    # -----------------------------------------------------------------
    # Document processing
    # -----------------------------------------------------------------

    uploaded_document_dir: str = Field(
        default=str(UPLOADED_DOCUMENT_DIR),
        validation_alias="UPLOADED_DOCUMENT_DIR",
    )

    processed_document_dir: str = Field(
        default=str(PROCESSED_DOCUMENT_DIR),
        validation_alias="PROCESSED_DOCUMENT_DIR",
    )

    max_upload_size: int = Field(
        default=10 * 1024 * 1024,
        validation_alias="MAX_UPLOAD_SIZE",
    )

    # -----------------------------------------------------------------
    # Whisper / Speech-to-Text
    # -----------------------------------------------------------------

    whisper_model: str = Field(
        default="base",
        validation_alias="WHISPER_MODEL",
    )

    # -----------------------------------------------------------------
    # Directory properties
    # -----------------------------------------------------------------

    @property
    def audio_dir(self) -> Path:
        """Directory used for audio files."""
        return AUDIO_DIR

    @property
    def temp_dir(self) -> Path:
        """Directory used for temporary files."""
        return TEMP_DIR

    @property
    def government_pdf_path(self) -> Path:
        """Government PDF directory as a Path."""
        return Path(self.government_pdf_dir)

    @property
    def uploaded_document_path(self) -> Path:
        """Uploaded document directory as a Path."""
        return Path(self.uploaded_document_dir)

    @property
    def processed_document_path(self) -> Path:
        """Processed document directory as a Path."""
        return Path(self.processed_document_dir)

    @property
    def vector_db_path_obj(self) -> Path:
        """Vector database directory as a Path."""
        return Path(self.vector_db_path)

    @property
    def directories(self) -> dict[str, Path]:
        """
        Return all application directories.
        """

        return {
            "base": BASE_DIR,
            "backend": BACKEND_DIR,
            "data": DATA_DIR,
            "government_pdfs": Path(
                self.government_pdf_dir
            ),
            "uploaded_documents": Path(
                self.uploaded_document_dir
            ),
            "processed_documents": Path(
                self.processed_document_dir
            ),
            "audio": AUDIO_DIR,
            "temp": TEMP_DIR,
            "vector_db": Path(
                self.vector_db_dir
            ),
        }


# ---------------------------------------------------------------------
# Global settings instance
# ---------------------------------------------------------------------

settings = Settings()


# ---------------------------------------------------------------------
# Ensure required directories exist
# ---------------------------------------------------------------------

DIRECTORIES = [
    DATA_DIR,
    Path(settings.government_pdf_dir),
    Path(settings.uploaded_document_dir),
    Path(settings.processed_document_dir),
    AUDIO_DIR,
    TEMP_DIR,
    Path(settings.vector_db_dir),
]

for directory in DIRECTORIES:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )