import time
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from llm_manager import LLMManager
from utils import logger

class RAGPipeline:
    """Handles vector retrieval, prompt building, LLM execution, and source extraction."""

    @staticmethod
    def format_context(docs: List[Document]) -> str:
        """Formats retrieved documents into a context block for the LLM prompt."""
        formatted_docs = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page", "Unknown")
            formatted_docs.append(
                f"[Doc {i+1}]: {source} (Page {page})\n"
                f"Content: {doc.page_content}\n"
                f"----------------------------------------"
            )
        return "\n\n".join(formatted_docs)

    @staticmethod
    def format_history(history: List[Dict[str, Any]], max_turns: int = 5) -> str:
        """Formats recent messages for history insertion into prompt."""
        formatted_turns = []
        # Each turn is user followed by assistant
        # Grab the last `max_turns * 2` messages
        recent_messages = history[-(max_turns * 2):]
        for msg in recent_messages:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            formatted_turns.append(f"{sender}: {msg['content']}")
        return "\n".join(formatted_turns)

    @classmethod
    def query(
        cls,
        query_text: str,
        vector_store: FAISS,
        llm_provider: str,
        llm_model: str,
        api_key: str = "",
        chat_history: List[Dict[str, Any]] = None,
        k: int = 5,
        stream_callback=None,
        stop_signal=None,
        temperature: float = 0.2,
        max_tokens: int = 1024
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """Runs the RAG flow: retrieves chunks with scores, queries LLM, and formats citations.
        
        Returns:
            A tuple of (answer_text, citations_list, duration)
        """
        start_time = time.time()
        
        if chat_history is None:
            chat_history = []

        logger.info(f"Retrieving top k={k} matching chunks from FAISS vector store...")
        # 1. Retrieve relevant chunks with scores
        docs_with_scores = vector_store.similarity_search_with_score(query_text, k=k)
        retrieved_docs = [doc for doc, _ in docs_with_scores]
        
        logger.info(f"Retrieved {len(docs_with_scores)} chunks. Extracting citations...")
        # 2. Extract citations with confidence score percentages
        citations = []
        seen = set()
        for doc, score in docs_with_scores:
            doc_name = doc.metadata.get("source", "Unknown Document")
            page_num = doc.metadata.get("page", 1)
            snippet = doc.page_content.strip()
            
            # Convert L2 distance score to confidence score
            confidence = float(max(0.0, min(1.0, 1.0 - (float(score) / 2.0))))
            
            # De-duplicate identical citations
            citation_key = (doc_name, page_num, snippet[:100])
            if citation_key not in seen:
                seen.add(citation_key)
                citations.append({
                    "document": doc_name,
                    "page": page_num,
                    "snippet": snippet,
                    "score": confidence
                })

        # 3. Format Prompt
        context_str = cls.format_context(retrieved_docs)
        history_str = cls.format_history(chat_history)
        
        system_instruction = (
            "You are DocMind AI, an intelligent desktop assistant. "
            "Your task is to answer the user's question using ONLY the provided context documents.\n"
            "If the context documents do NOT contain the information needed to answer, "
            "honestly reply: \"I cannot find the answer to this question in the uploaded documents.\"\n"
            "Do not make up facts or use outside knowledge. Keep your answer professional, concise and accurate.\n\n"
            f"CONTEXT DOCUMENTS:\n{context_str}\n\n"
            f"CONVERSATION HISTORY:\n{history_str}\n\n"
            f"USER QUESTION: {query_text}\n\n"
            "ASSISTANT ANSWER:"
        )

        # 4. Invoke LLM (Supporting streaming or invoke)
        try:
            logger.info(f"Contacting LLM provider '{llm_provider}' using model '{llm_model}'...")
            llm = LLMManager.get_llm(
                provider=llm_provider,
                model_name=llm_model,
                api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            if stream_callback:
                answer = ""
                for chunk in llm.stream(system_instruction):
                    # Check for stop signal
                    if stop_signal and stop_signal():
                        logger.info("LLM streaming stopped by user signal.")
                        break
                    
                    content = chunk.content
                    answer += content
                    stream_callback(content)
            else:
                response = llm.invoke(system_instruction)
                answer = response.content.strip()
        except Exception as e:
            logger.exception("Error occurred during LLM query execution.")
            raise e

        duration = time.time() - start_time
        logger.info(f"RAG query finished. Response time: {duration:.2f}s")
        return answer, citations, duration
