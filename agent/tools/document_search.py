from typing import Dict, Any, Optional
from agent.tools.base import BaseTool
from agent.models import ToolResult
from rag_pipeline import RAGPipeline
from vector_store import VectorStoreManager
from embeddings import EmbeddingManager
from database import DatabaseManager

class DocumentSearchTool(BaseTool):
    """Tool that queries the Phase 2B hybrid RAG pipeline for document evidence."""

    @property
    def name(self) -> str:
        return "document_search"

    @property
    def description(self) -> str:
        return "Searches uploaded document collection using hybrid FAISS+BM25 retrieval, cross-encoder reranking, and citation validation."

    @property
    def permissions(self) -> Dict[str, bool]:
        return {
            "read_documents": True,
            "internet_access": False,
            "calculation": False,
            "database_access": True
        }

    def execute(self, input_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ToolResult:
        query_text = input_data.get("query", "").strip()
        if not query_text:
            return ToolResult(tool_name=self.name, status="error", error_message="Query parameter is required.")

        ctx = context or {}
        user_id = ctx.get("user_id", 1)
        doc_ids = ctx.get("selected_doc_ids")

        user_docs = DatabaseManager.get_documents(user_id)
        user_doc_ids = set(d["id"] for d in user_docs)

        if not doc_ids:
            doc_ids = list(user_doc_ids)
        else:
            # Enforce authorization: only allow doc_ids owned by user_id
            doc_ids = [did for did in doc_ids if did in user_doc_ids]

        if not doc_ids:
            return ToolResult(
                tool_name=self.name,
                status="success",
                data={"answer": "No documents found in library.", "citations": [], "results": []}
            )


        user_settings = DatabaseManager.get_settings(user_id)
        provider = ctx.get("llm_provider") or user_settings.get("llm_provider", "Ollama")
        model = ctx.get("llm_model") or user_settings.get("llm_model", "llama3")
        api_key = ctx.get("api_key") or user_settings.get("api_key", "")
        embed_name = user_settings.get("embedding_model", "all-MiniLM-L6-v2")

        try:
            embed_model = EmbeddingManager.get_embeddings(embed_name, api_key)
            vector_store = VectorStoreManager.load_merged_vector_store(user_id, doc_ids, embed_model)
            bm25_index = VectorStoreManager.load_merged_bm25_store(user_id, doc_ids)

            answer, citations, duration = RAGPipeline.query(
                query_text=query_text,
                vector_store=vector_store,
                llm_provider=provider,
                llm_model=model,
                api_key=api_key,
                chat_history=ctx.get("chat_history", []),
                bm25_index=bm25_index,
                stream_callback=ctx.get("stream_callback"),
                stop_signal=ctx.get("stop_signal")
            )


            return ToolResult(
                tool_name=self.name,
                status="success",
                data={
                    "answer": answer,
                    "citations": citations,
                    "doc_count": len(doc_ids),
                    "duration": duration
                }
            )
        except Exception as e:
            return ToolResult(tool_name=self.name, status="error", error_message=f"Document search error: {str(e)}")
