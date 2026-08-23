import time
from typing import List, Dict, Any, Tuple, Optional
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from llm_manager import LLMManager
from utils import logger
from retrieval.hybrid_retriever import HybridRetriever
from retrieval.bm25_store import BM25Index
from retrieval.reranker import Reranker
from retrieval.citation_validator import CitationValidator
from retrieval.models import RetrievedChunk

class RAGPipeline:
    """Handles two-stage hybrid retrieval (FAISS + BM25 + Cross-Encoder Rerank), prompt building, LLM execution, and citation validation."""

    @staticmethod
    def format_history(history: List[Dict[str, Any]], max_turns: int = 5) -> str:
        """Formats recent messages for history insertion into prompt."""
        formatted_turns = []
        recent_messages = history[-(max_turns * 2):]
        for msg in recent_messages:
            sender = "User" if msg["sender"] == "user" else "Assistant"
            formatted_turns.append(f"{sender}: {msg['content']}")
        return "\n".join(formatted_turns)

    @classmethod
    def query(
        cls,
        query_text: str,
        vector_store: Optional[FAISS],
        llm_provider: str,
        llm_model: str,
        api_key: str = "",
        chat_history: List[Dict[str, Any]] = None,
        k: int = 5,
        stream_callback=None,
        stop_signal=None,
        temperature: float = 0.2,
        max_tokens: int = 1024,
        bm25_index: Optional[BM25Index] = None,
        enable_reranker: bool = True
    ) -> Tuple[str, List[Dict[str, Any]], float]:
        """Runs the two-stage RAG flow: 
        1. Hybrid retrieval (Dense FAISS + Lexical BM25 via RRF) -> candidates
        2. Second-stage Cross-Encoder reranking -> top-k best evidence chunks
        3. Assigns stable evidence tags (DOC-1, DOC-2, ...)
        4. Queries LLM with grounded prompt
        5. Extracts and deterministically validates citations
        
        Returns:
            A tuple of (answer_text, citations_list, duration)
        """
        start_time = time.time()
        
        if chat_history is None:
            chat_history = []

        candidate_k = max(15, k * 3)
        logger.info(f"Executing Stage 1: Hybrid Retrieval (Dense + BM25) for query, fetching top {candidate_k} candidates...")
        
        # Stage 1: Hybrid First-Stage Retrieval (Dense FAISS + Lexical BM25 with RRF)
        retriever = HybridRetriever(vector_store=vector_store, bm25_index=bm25_index)
        candidate_chunks = retriever.retrieve(query_text, top_k=candidate_k)

        # Stage 2: Second-Stage Cross-Encoder Reranking
        logger.info(f"Executing Stage 2: Cross-Encoder Reranking over {len(candidate_chunks)} candidates...")
        reranker = Reranker(enabled=enable_reranker)
        reranked_chunks = reranker.rerank(query_text, candidate_chunks, top_k=k)

        # Stage 3: Assign Stable Evidence IDs & Build Context
        evidence_text, evidence_map = CitationValidator.build_evidence_context(reranked_chunks)
        history_str = cls.format_history(chat_history)
        
        system_instruction = (
            "You are DocMind AI, an intelligent assistant. "
            "Your task is to answer the user's question using ONLY the provided context evidence.\n\n"
            "CRITICAL CITATION RULES:\n"
            "1. Every statement or claim drawing from a document MUST be followed by its citation tag, e.g. [CITE:DOC-1] or [CITE:DOC-2].\n"
            "2. Use ONLY the evidence tags [DOC-1], [DOC-2], etc. provided in the CONTEXT EVIDENCE section below. Never invent citation tags or page numbers.\n"
            "3. If the provided context evidence does NOT contain sufficient information to answer the question, "
            "honestly reply: \"I cannot find sufficient evidence in the uploaded documents to answer this question.\"\n"
            "4. Keep your answer professional, concise and accurate.\n\n"
            f"--- CONTEXT EVIDENCE START ---\n{evidence_text}\n--- CONTEXT EVIDENCE END ---\n\n"
            f"CONVERSATION HISTORY:\n{history_str}\n\n"
            f"USER QUESTION: {query_text}\n\n"
            "ASSISTANT ANSWER:"
        )

        # Stage 4: Invoke LLM
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
                for chunk_token in llm.stream(system_instruction):
                    if stop_signal and stop_signal():
                        logger.info("LLM streaming stopped by user signal.")
                        break
                    
                    content = chunk_token.content
                    answer += content
                    stream_callback(content)
            else:
                response = llm.invoke(system_instruction)
                answer = response.content.strip()
        except Exception as e:
            logger.exception("Error occurred during LLM query execution.")
            err_str = str(e)
            if "10061" in err_str or "Connection refused" in err_str or "Failed to establish a new connection" in err_str:
                raise RuntimeError(
                    f"LLM Provider '{llm_provider}' is unreachable on http://localhost:11434. "
                    "Please ensure local Ollama service is running, or set GROQ_API_KEY / OPENAI_API_KEY environment variables."
                ) from e
            raise e


        # Stage 5: Deterministic Citation Extraction & Validation
        citations, validity_rate, coverage_rate = CitationValidator.extract_and_validate(answer, evidence_map)
        logger.info(f"Citation validation complete. Extracted: {len(citations)}, Validity Rate: {validity_rate*100:.1f}%")

        duration = time.time() - start_time
        logger.info(f"Two-stage RAG query finished in {duration:.2f}s")
        return answer, citations, duration


