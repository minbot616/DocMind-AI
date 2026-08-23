from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_current_user_id
from backend.schemas.conversations import (
    ConversationResponse,
    ConversationListResponse,
    CreateConversationRequest
)
from backend.services.conversation_service import conversation_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])

@router.get("", response_model=ConversationListResponse)
def list_conversations(user_id: int = Depends(get_current_user_id)):
    """List all saved conversation sessions for the user."""
    return conversation_service.list_conversations(user_id=user_id)

@router.get("/{conversation_id}", response_model=ConversationResponse)
def get_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Retrieve details and full message history for a specific conversation session."""
    conv = conversation_service.get_conversation(conversation_id)
    if not conv or getattr(conv, "user_id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )
    return conv

@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(
    request: CreateConversationRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Create a new conversation session."""
    return conversation_service.create_conversation(
        title=request.title,
        user_id=user_id
    )

@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Delete a conversation session and all associated messages."""
    conv = conversation_service.get_conversation(conversation_id)
    if not conv or getattr(conv, "user_id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )

    success = conversation_service.delete_conversation(conversation_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with ID {conversation_id} not found."
        )
    return None


