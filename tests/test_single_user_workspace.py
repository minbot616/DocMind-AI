from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_single_user_documents_endpoint():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data

def test_single_user_conversations_endpoint():
    response = client.get("/conversations")
    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data

    # Create new conversation
    c_resp = client.post("/conversations", json={"title": "Single User Test Chat"})
    assert c_resp.status_code == 201
    c_data = c_resp.json()
    assert c_data["title"] == "Single User Test Chat"

def test_single_user_chat_validation():
    # Blank query validation
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 400

def test_settings_provider_models():
    resp_ollama = client.get("/settings/models?provider=Ollama")
    assert resp_ollama.status_code == 200
    assert "models" in resp_ollama.json()

    resp_groq = client.get("/settings/models?provider=Groq")
    assert resp_groq.status_code == 200
    assert "llama-3.1-8b-instant" in resp_groq.json()["models"]

    resp_openai = client.get("/settings/models?provider=OpenAI")
    assert resp_openai.status_code == 200
    assert "gpt-4o-mini" in resp_openai.json()["models"]

def test_settings_connection_test():
    # Attempt connection test with invalid provider/key
    resp = client.post("/settings/test-connection", json={"llm_provider": "Groq", "llm_model": "llama-3.1-8b-instant", "api_key": ""})
    assert resp.status_code == 200
    data = resp.json()
    assert "success" in data
    assert data["success"] is False

