from fastapi import APIRouter, Depends, HTTPException, status
from backend.api.dependencies import get_current_user_id
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("", response_model=ChatResponse)
def send_chat_message(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id)
):
    """Process a query through the RAG pipeline and return the assistant answer and source citations."""
    if request.user_id is None:
        request.user_id = user_id
    try:
        return chat_service.process_message(request)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"RAG query execution failed: {str(e)}")
