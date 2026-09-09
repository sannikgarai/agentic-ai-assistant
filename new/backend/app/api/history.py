
"""
Conversation history API routes.

Handles retrieving and managing the user's conversation history
using the Supabase repository layer.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.app.core.security import get_current_user
from backend.app.database.repositories.conversations import (
    ConversationRepository,
)
from backend.app.database.repositories.messages import (
    MessageRepository,
)


router = APIRouter()

conversation_repository = ConversationRepository()
message_repository = MessageRepository()


# --------------------------------------------------
# Conversation History
# --------------------------------------------------

@router.get("/")
async def get_history(
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return conversation history for the current user.
    """

    user_id = str(user["id"])

    conversations = (
        conversation_repository.list_for_user(
            user_id=user_id,
            limit=50,
        )
    )

    return {
        "success": True,
        "user_id": user_id,
        "conversations": conversations,
    }


# --------------------------------------------------
# Single Conversation
# --------------------------------------------------

@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Return a specific conversation and its messages.
    """

    user_id = str(user["id"])

    conversation = (
        conversation_repository.get(
            conversation_id=conversation_id,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    if str(conversation.get("user_id")) != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this conversation.",
        )

    messages = (
        message_repository.list_for_conversation(
            conversation_id=conversation_id,
            limit=100,
        )
    )

    return {
        "success": True,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "conversation": conversation,
        "messages": messages,
    }


# --------------------------------------------------
# Delete Conversation
# --------------------------------------------------

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict[str, Any] = Depends(
        get_current_user
    ),
):
    """
    Delete a conversation belonging to the current user.
    """

    user_id = str(user["id"])

    conversation = (
        conversation_repository.get(
            conversation_id=conversation_id,
        )
    )

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    if str(conversation.get("user_id")) != user_id:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this conversation.",
        )

    deleted = (
        conversation_repository.delete(
            conversation_id=conversation_id,
        )
    )

    if not deleted:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete conversation.",
        )

    return {
        "success": True,
        "conversation_id": conversation_id,
        "user_id": user_id,
        "message": "Conversation deleted successfully.",
    }
