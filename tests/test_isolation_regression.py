import os
import pytest
from backend.database.config import assert_not_production_db, get_engine
from backend.core.config import settings
from database import DatabaseManager

def test_production_guard_refuses_prod_db():
    """Test A: Verify production guard raises RuntimeError if DATABASE_URL points to production database."""
    prod_url = "postgresql+psycopg://postgres:postgres@localhost:5432/docmind_db"
    with pytest.raises(RuntimeError, match="Refusing to run tests against the production database"):
        assert_not_production_db(prod_url)

def test_test_document_created_in_test_database_only():
    """Test B & C: Verify test documents are created ONLY in the isolated test database and test storage."""
    # Ensure test storage directory is isolated
    assert "docmind_test_storage" in settings.DOCUMENTS_DIR
    assert settings.DOCUMENTS_DIR != os.path.join(settings.BASE_DIR, "documents")

    # Add test document record
    doc_id = DatabaseManager.add_document(
        user_id=1,
        filename="isolated_test_sample.pdf",
        file_path=os.path.join(settings.DOCUMENTS_DIR, "isolated_test_sample.pdf"),
        file_type="PDF",
        file_size=1024
    )
    assert doc_id is not None
    
    # Retrieve doc from test DB
    docs = DatabaseManager.get_documents(user_id=1)
    filenames = [d["filename"] for d in docs]
    assert "isolated_test_sample.pdf" in filenames

def test_pytest_does_not_create_test_document_in_prod_path():
    """Test D & E: Verify test storage is isolated from production path."""
    prod_docs_dir = os.path.join(settings.BASE_DIR, "documents")
    prod_test_file = os.path.join(prod_docs_dir, "DocMind_AI_RAG_Test_Document.pdf")
    
    # Assert tests do not write into production documents folder
    assert not os.path.exists(prod_test_file)
