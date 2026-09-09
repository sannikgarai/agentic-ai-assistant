"""
Embedding generation.

Uses SentenceTransformers to convert document chunks and
queries into dense vectors.

The SentenceTransformer library and model are loaded lazily
so the backend does not load PyTorch during application startup.
"""

from **future** import annotations

from typing import Sequence

import numpy as np

from backend.app.core.config import settings

class EmbeddingModel:
"""Sentence-transformers embedding model."""

```
def __init__(
    self,
    model_name: str | None = None,
):
    self.model_name = (
        model_name
        or settings.embedding_model
    )

    self._model = None

@property
def model(self):
    """
    Load the SentenceTransformer library and model lazily.

    This prevents PyTorch and the embedding model from being
    loaded during FastAPI startup.
    """

    if self._model is None:
        from sentence_transformers import (
            SentenceTransformer,
        )

        self._model = SentenceTransformer(
            self.model_name
        )

    return self._model

def encode(
    self,
    texts: Sequence[str],
    normalize: bool = True,
) -> np.ndarray:
    """Generate embeddings for multiple texts."""

    if not texts:
        return np.empty(
            (0, self.dimension),
            dtype=np.float32,
        )

    embeddings = self.model.encode(
        list(texts),
        convert_to_numpy=True,
        normalize_embeddings=normalize,
        show_progress_bar=False,
    )

    return np.asarray(
        embeddings,
        dtype=np.float32,
    )

def encode_query(
    self,
    query: str,
) -> np.ndarray:
    """Generate an embedding for a query."""

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    embedding = self.encode(
        [query],
        normalize=True,
    )

    return embedding[0]

@property
def dimension(self) -> int:
    """Return embedding dimensionality."""

    return int(
        self.model.get_sentence_embedding_dimension()
    )
```

"""

After replacing it:

```powershell
git add new/backend/app/rag/embeddings.py
git commit -m "Lazy load sentence transformer"
git push origin main
```

Then Render will automatically deploy.

**Do not change `requirements.txt` yet.** We are fixing the startup memory issue systematically.
