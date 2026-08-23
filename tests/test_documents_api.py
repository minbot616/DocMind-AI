from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_list_documents_endpoint():
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)

def test_get_nonexistent_document():
    response = client.get("/documents/999999")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
