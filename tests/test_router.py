import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.router import IntentRouter

def test_intent_router_classification():
    # Document library metadata
    dec2 = IntentRouter.route("how many documents do I have?")
    assert dec2.intent == "document_metadata"
    assert "document_metadata" in dec2.recommended_tools

    # Web search
    dec3 = IntentRouter.route("search web for latest AI news")
    assert dec3.intent == "web_search"
    assert "web_search" in dec3.recommended_tools

    # Conversational greeting
    dec4 = IntentRouter.route("hello")
    assert dec4.intent == "general"
    assert dec4.recommended_tools == []

    # Document content query with documents present
    dec5 = IntentRouter.route("What is the architecture of the system?", context={"selected_doc_ids": [1]})
    assert dec5.intent == "document_search"
    assert "document_search" in dec5.recommended_tools
