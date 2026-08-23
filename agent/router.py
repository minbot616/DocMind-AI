import re
from typing import Dict, Any, List, Optional
from agent.models import RouterDecision

class IntentRouter:
    """Classifies user queries into finite tool execution intents using deterministic & pattern-matching rules."""

    @staticmethod
    def route(query: str, context: Optional[Dict[str, Any]] = None) -> RouterDecision:
        """Determines which tool(s) to invoke based on user prompt and context."""
        if not query or not query.strip():
            return RouterDecision(intent="general", recommended_tools=[], reasoning="Empty query defaulted to general.")

        q_lower = query.strip().lower()
        ctx = context or {}
        has_documents = bool(ctx.get("selected_doc_ids") or ctx.get("has_documents"))

        # 1. Document Library Metadata Queries
        meta_keywords = ["how many documents", "list my files", "list my docs", "uploaded documents", "show my library", "file inventory", "pages count"]
        if any(kw in q_lower for kw in meta_keywords):
            return RouterDecision(
                intent="document_metadata",
                recommended_tools=["document_metadata"],
                reasoning="Query asks for document library metadata or inventory."
            )

        # 2. Explicit Web Search Queries
        web_keywords = ["search web", "latest news", "current price", "today's weather", "who is the current", "online search"]
        if any(kw in q_lower for kw in web_keywords):
            return RouterDecision(
                intent="web_search",
                recommended_tools=["web_search"],
                reasoning="Query explicitly requests live internet web search."
            )

        # 3. Conversational / Greetings / Direct Knowledge
        greeting_keywords = ["hello", "hi", "hey", "who are you", "thank you", "thanks", "good morning", "good evening"]
        if q_lower in greeting_keywords or (len(q_lower.split()) <= 2 and any(kw in q_lower for kw in greeting_keywords)):
            return RouterDecision(
                intent="general",
                recommended_tools=[],
                reasoning="Conversational greeting routed directly to LLM."
            )

        # 4. Default to Document Search if user has uploaded documents, otherwise General
        if has_documents:
            return RouterDecision(
                intent="document_search",
                recommended_tools=["document_search"],
                reasoning="Document context available; routing query to document search."
            )

        return RouterDecision(
            intent="general",
            recommended_tools=[],
            reasoning="No documents available; routing to general LLM response."
        )
