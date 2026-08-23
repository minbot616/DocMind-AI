import sys
from typing import List, Optional, Any, Callable
from backend.core.config import settings


# Ensure root workspace modules are importable
if settings.BASE_DIR not in sys.path:
    sys.path.insert(0, settings.BASE_DIR)

from database import DatabaseManager
from chat_manager import ChatManager
from rag_pipeline import RAGPipeline
from embeddings import EmbeddingManager
from vector_store import VectorStoreManager
from agent.orchestrator import AgentOrchestrator
from backend.schemas.chat import ChatRequest, ChatResponse, CitationSchema

class ChatService:

    @staticmethod
    def process_message(
        request: ChatRequest,
        stream_callback: Optional[Any] = None,
        stop_signal: Optional[Any] = None
    ) -> ChatResponse:
        user_id = request.user_id if request.user_id is not None else 1
        query_text = request.message.strip()

        if not query_text:
            raise ValueError("Message content cannot be empty.")

        # 1. Lazy create conversation if not provided
        chat_id = request.conversation_id
        clean_text = query_text.replace("\n", " ").strip()
        words = clean_text.split()
        generated_title = " ".join(words[:6]) if len(words) > 6 else clean_text
        if len(generated_title) > 40:
            generated_title = generated_title[:37] + "..."

        if chat_id is None:
            try:
                chat_id = ChatManager.create_new_chat(user_id, generated_title)
            except Exception as e:
                from utils import logger
                logger.warning(f"Failed to create chat with title '{generated_title}', falling back to default: {e}")
                chat_id = ChatManager.create_new_chat(user_id, "New Conversation")
        else:
            try:
                chat = DatabaseManager.get_chat(chat_id)
                if chat and (chat.get("title") == "New Conversation" or not chat.get("title")):
                    ChatManager.rename_chat(chat_id, generated_title)
            except Exception as e:
                from utils import logger
                logger.warning(f"Non-fatal error updating chat title: {e}")


        # 2. Record User Message in Database
        ChatManager.save_message(chat_id, "user", query_text)

        # 3. Retrieve Conversation History & Persistent Summary
        all_messages = ChatManager.get_chat_messages(chat_id)
        if all_messages and all_messages[-1]["sender"] == "user":
            all_messages = all_messages[:-1]

        existing_summary = ChatManager.get_chat_summary(chat_id)
        user_settings = DatabaseManager.get_settings(user_id)
        provider = user_settings.get("llm_provider", settings.DEFAULT_LLM_PROVIDER)
        model = user_settings.get("llm_model", settings.DEFAULT_LLM_MODEL)
        api_key = user_settings.get("api_key", "")

        # 4. Assemble Token-Aware Context & Update Summary
        from memory.context_manager import ContextManager
        ctx_manager = ContextManager()
        memory_state, updated_summary = ctx_manager.assemble_memory(
            conversation_id=chat_id,
            all_messages=all_messages,
            existing_summary=existing_summary,
            llm_provider=provider,
            llm_model=model,
            api_key=api_key
        )

        if updated_summary != existing_summary and updated_summary:
            ChatManager.update_chat_summary(chat_id, updated_summary)

        # 5. Assemble Agent Execution Context with Token-Budgeted Memory State
        context = {
            "user_id": user_id,
            "selected_doc_ids": request.selected_doc_ids,
            "chat_history": memory_state.recent_messages,
            "conversation_summary": memory_state.summary,
            "stream_callback": stream_callback,
            "stop_signal": stop_signal
        }


        # 6. Route query through Controlled Agent Orchestrator
        orchestrator = AgentOrchestrator()
        response = orchestrator.process(query=query_text, context=context)

        # 7. Save Assistant Message and Sources to DB
        ChatManager.save_message(chat_id, "assistant", response.answer, response.citations, response.duration)

        citation_models = [CitationSchema(**c) for c in response.citations] if response.citations else []
        return ChatResponse(
            answer=response.answer,
            conversation_id=chat_id,
            sources=citation_models,
            tools_used=response.tools_used,
            response_time=response.duration
        )


chat_service = ChatService()

