"""
Memory package.

Provides:
- Conversation management
- Short-term conversational memory
- Long-term persistent memory
- Multimodal memory
- Memory retrieval
"""

from backend.app.memory.conversation import (
    Conversation,
    ConversationManager,
    ConversationMessage,
)

from backend.app.memory.short_term import (
    ShortTermMemory,
)

from backend.app.memory.long_term import (
    LongTermMemory,
)

from backend.app.memory.multimodal import (
    MultimodalMemory,
    MultimodalMemoryItem,
)

from backend.app.memory.retriever import (
    MemoryRetriever,
    MemorySearchResult,
)

__all__ = [
    "Conversation",
    "ConversationMessage",
    "ConversationManager",
    "ShortTermMemory",
    "LongTermMemory",
    "MultimodalMemory",
    "MultimodalMemoryItem",
    "MemoryRetriever",
    "MemorySearchResult",
]