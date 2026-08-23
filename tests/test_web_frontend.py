from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_web_index_route():
    response = client.get("/")
    assert response.status_code == 200
    assert "DocMind AI" in response.text

def test_static_css_route():
    response = client.get("/static/css/styles.css")
    assert response.status_code == 200
    assert "--bg-dark" in response.text
