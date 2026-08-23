import time
import logging
from typing import Dict, Any, List, Optional
from agent.registry import ToolRegistry, default_registry
from agent.router import IntentRouter
from agent.models import AgentResponse, ToolResult
from llm_manager import LLMManager
from database import DatabaseManager

logger = logging.getLogger("DocMindBackend")

class AgentOrchestrator:
    """Controlled Orchestrator managing query routing, bounded tool execution (MAX_TOOL_CALLS=3), and LLM synthesis."""

    def __init__(self, registry: Optional[ToolRegistry] = None, max_tool_calls: int = 3):
        self.registry = registry or default_registry
        self.max_tool_calls = max_tool_calls

    def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Executes controlled agent pipeline for user query."""
        start_time = time.time()
        ctx = context or {}
        user_id = ctx.get("user_id", 1)

        # Ensure document availability context is populated
        if "has_documents" not in ctx:
            docs = DatabaseManager.get_documents(user_id)
            ctx["has_documents"] = len(docs) > 0
            if "selected_doc_ids" not in ctx or ctx["selected_doc_ids"] is None:
                ctx["selected_doc_ids"] = [d["id"] for d in docs]

        # 1. Intent Routing
        decision = IntentRouter.route(query, ctx)
        logger.info(f"Agent Orchestrator router decision: intent='{decision.intent}', tools={decision.recommended_tools}")

        tools_used: List[Dict[str, Any]] = []
        tool_results: List[ToolResult] = []
        tool_call_count = 0

        # 2. Bounded Tool Execution Loop (MAX_TOOL_CALLS = 3)
        for tool_name in decision.recommended_tools:
            if tool_call_count >= self.max_tool_calls:
                logger.warning(f"Reached MAX_TOOL_CALLS limit ({self.max_tool_calls}). Stopping further tool execution.")
                break

            tool_input = {"query": query}
            result = self.registry.execute_tool(tool_name, tool_input, ctx)
            tool_call_count += 1

            tool_results.append(result)
            tools_used.append({
                "name": tool_name,
                "status": result.status,
                "data": result.data if result.status == "success" else {},
                "error": result.error_message
            })

        # 3. Controlled Synthesis based on Intent and Tool Execution Output
        final_answer = ""
        citations: List[Dict[str, Any]] = []

        # Case A: Document Search Tool Executed
        doc_search_res = next((r for r in tool_results if r.tool_name == "document_search" and r.status == "success"), None)
        if doc_search_res:
            final_answer = doc_search_res.data.get("answer", "")
            citations = doc_search_res.data.get("citations", [])

        # Case B: Standalone Document Metadata Tool Executed
        elif any(r.tool_name == "document_metadata" for r in tool_results):
            meta_res = next((r for r in tool_results if r.tool_name == "document_metadata"), None)
            if meta_res and meta_res.status == "success":
                data = meta_res.data
                total_docs = data.get("total_documents", 0)
                total_pages = data.get("total_pages", 0)
                total_chunks = data.get("total_chunks", 0)
                docs_list = data.get("documents", [])

                lines = [f"### 📚 Knowledge Base Summary ({total_docs} documents, {total_pages} pages, {total_chunks} indexed sections)\n"]
                for d in docs_list:
                    size_kb = d.get('file_size_kb') if d.get('file_size_kb') is not None else round(d.get('file_size', 0)/1024, 1)
                    lines.append(f"- **{d.get('filename', 'File')}** (Format: {d.get('file_type', 'PDF')}, Pages: {d.get('pages', 0)}, Sections: {d.get('chunks', 0)}, Size: {size_kb} KB)")
                final_answer = "\n".join(lines)


            else:
                final_answer = "Could not retrieve knowledge base metadata."

        # Case C: Standalone Web Search Tool Executed
        elif any(r.tool_name == "web_search" for r in tool_results):
            web_res = next((r for r in tool_results if r.tool_name == "web_search"), None)
            if web_res and web_res.status == "success":
                search_results = web_res.data.get("results", [])
                snippets = []
                for idx, item in enumerate(search_results[:3]):
                    title = item.get("title", "")
                    body = item.get("snippet", "")
                    link = item.get("link", "")
                    snippets.append(f"[{idx+1}] {title}\n{body}\nSource: {link}")
                
                prompt = (
                    "Synthesize a concise answer for the user query using the following web search evidence. "
                    "Include numbered citation references like [1], [2] corresponding to the sources.\n\n"
                    f"SEARCH EVIDENCE:\n{chr(10).join(snippets)}\n\n"
                    f"USER QUERY: {query}\n\nANSWER:"
                )
                user_settings = DatabaseManager.get_settings(user_id)
                provider = ctx.get("llm_provider") or user_settings.get("llm_provider", "Ollama")
                model = ctx.get("llm_model") or user_settings.get("llm_model", "llama3")
                api_key = ctx.get("api_key") or user_settings.get("api_key", "")

                stream_cb = ctx.get("stream_callback")
                stop_sig = ctx.get("stop_signal")

                try:
                    llm = LLMManager.get_llm(provider, model, api_key, user_id=user_id)
                    if stream_cb:
                        final_answer = ""
                        for chunk_token in llm.stream(prompt):
                            if stop_sig and stop_sig():
                                break
                            content = chunk_token.content
                            final_answer += content
                            stream_cb(content)
                    else:
                        resp = llm.invoke(prompt)
                        final_answer = resp.content.strip()
                except Exception as e:
                    final_answer = f"Web search synthesis error: {str(e)}"
            else:
                final_answer = "Web search provider unavailable."

        # Case D: General Conversation (Direct LLM)
        else:
            user_settings = DatabaseManager.get_settings(user_id)
            provider = ctx.get("llm_provider") or user_settings.get("llm_provider", "Ollama")
            model = ctx.get("llm_model") or user_settings.get("llm_model", "llama3")
            api_key = ctx.get("api_key") or user_settings.get("api_key", "")
            stream_cb = ctx.get("stream_callback")
            stop_sig = ctx.get("stop_signal")

            try:
                llm = LLMManager.get_llm(provider, model, api_key, user_id=user_id)
                prompt = f"You are DocMind AI, a helpful assistant. Answer concisely:\nUser: {query}\nAssistant:"
                if stream_cb:
                    final_answer = ""
                    for chunk_token in llm.stream(prompt):
                        if stop_sig and stop_sig():
                            break
                        content = chunk_token.content
                        final_answer += content
                        stream_cb(content)
                else:
                    resp = llm.invoke(prompt)
                    final_answer = resp.content.strip()
            except Exception as e:
                final_answer = f"AI service error: {str(e)}"

        duration = round(time.time() - start_time, 3)

        return AgentResponse(
            answer=final_answer,
            citations=citations,
            tools_used=tools_used,
            duration=duration
        )

