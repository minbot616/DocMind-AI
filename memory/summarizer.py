import logging
from typing import List, Dict, Any, Optional
from memory.token_counter import TokenCounter
from llm_manager import LLMManager

logger = logging.getLogger("DocMindBackend")

class ConversationSummarizer:
    """Generates compressed conversation summaries when history exceeds token thresholds."""

    def __init__(self, summarization_threshold: int = 800):
        self.summarization_threshold = summarization_threshold

    def should_summarize(self, messages: List[Dict[str, Any]]) -> bool:
        """Determines if conversation history is large enough to warrant summarization."""
        total_tokens = TokenCounter.count_messages_tokens(messages)
        return total_tokens >= self.summarization_threshold

    def summarize_messages(
        self,
        older_messages: List[Dict[str, Any]],
        existing_summary: Optional[str] = None,
        llm_provider: str = "Ollama",
        llm_model: str = "llama3",
        api_key: str = ""
    ) -> Optional[str]:
        """Summarizes older conversation turns using the configured LLM, with fallback protection."""
        if not older_messages:
            return existing_summary

        turns_text = "\n".join([f"{msg.get('sender', 'User')}: {msg.get('content', '')}" for msg in older_messages])
        prev_sum = existing_summary or "None"

        prompt = (
            "You are an expert conversation summarizer.\n"
            "Summarize the conversation history concisely, preserving key facts, user goals, numeric values, document references, and decisions.\n"
            "Do NOT include conversational filler. Keep the summary under 150 words.\n\n"
            f"EXISTING SUMMARY:\n{prev_sum}\n\n"
            f"OLDER CONVERSATION TURNS:\n{turns_text}\n\n"
            "UPDATED SUMMARY:"
        )

        try:
            logger.info(f"Generating conversation summary over {len(older_messages)} older turns...")
            llm = LLMManager.get_llm(provider=llm_provider, model_name=llm_model, api_key=api_key, temperature=0.1)
            response = llm.invoke(prompt)
            summary_text = response.content.strip()

            if summary_text and len(summary_text) > 10:
                logger.info("Conversation summary generated successfully.")
                return summary_text
            return existing_summary
        except Exception as e:
            logger.warning(f"Conversation summarization failed: {str(e)}. Preserving existing summary.")
            return existing_summary
