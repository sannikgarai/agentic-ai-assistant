from **future** import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.history import router as history_router
from app.api.verification import router as verification_router
from app.api.voice import router as voice_router
from app.core.config import settings
from app.core.logging import configure_logging

# --------------------------------------------------

# Logging

# --------------------------------------------------

configure_logging()

# --------------------------------------------------

# Application Startup / Shutdown

# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
"""
Application startup and shutdown handler.
"""

```
print(
    "Starting Agentic AI Assistant Backend..."
)

yield

print(
    "Shutting down Agentic AI Assistant Backend..."
)
```

# --------------------------------------------------

# FastAPI Application

# --------------------------------------------------

app = FastAPI(
title=settings.app_name,
description=(
"Backend API for a multilingual Agentic AI "
"Assistant with RAG, document processing, "
"verification, voice processing, and "
"step-by-step user guidance."
),
version=settings.app_version,
debug=settings.debug,
lifespan=lifespan,
)

# --------------------------------------------------

# CORS Configuration

# --------------------------------------------------

app.add_middleware(
CORSMiddleware,
allow_origins=[
settings.frontend_url,
"http://localhost:5173",
"http://127.0.0.1:5173",
],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)

# --------------------------------------------------

# Health Check

# --------------------------------------------------

@app.get(
"/",
tags=["Health"],
)
async def root():
"""Root health endpoint."""

```
return {
    "message": (
        "Agentic AI Assistant Backend "
        "is running"
    ),
    "version": settings.app_version,
    "status": "healthy",
}
```

@app.get(
"/health",
tags=["Health"],
)
async def health_check():
"""Backend health check."""

```
return {
    "status": "healthy",
    "service": (
        "agentic-ai-assistant-backend"
    ),
    "version": settings.app_version,
}
```

# --------------------------------------------------

# API Routers

# --------------------------------------------------

app.include_router(
chat_router,
prefix="/api/chat",
tags=["Chat"],
)

app.include_router(
voice_router,
prefix="/api/voice",
tags=["Voice"],
)

app.include_router(
documents_router,
prefix="/api/documents",
tags=["Documents"],
)

app.include_router(
verification_router,
prefix="/api/verification",
tags=["Verification"],
)

app.include_router(
history_router,
prefix="/api/history",
tags=["History"],
)

# --------------------------------------------------

# Run Directly

# --------------------------------------------------

if **name** == "**main**":
import uvicorn

```
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8000,
    reload=settings.debug,
)
```
