import os
import sys
import tempfile
import pytest

# 1. Enforce test flag environment variable
os.environ["TESTING"] = "true"

# 2. Configure isolated temporary test document and vector storage directories
tmp_test_dir = tempfile.mkdtemp(prefix="docmind_test_storage_")
test_docs_dir = os.path.join(tmp_test_dir, "documents")
test_vecs_dir = os.path.join(tmp_test_dir, "vectors")
os.makedirs(test_docs_dir, exist_ok=True)
os.makedirs(test_vecs_dir, exist_ok=True)

os.environ["DOCMIND_DOCUMENTS_DIR"] = test_docs_dir
os.environ["DOCMIND_VECTOR_DIR"] = test_vecs_dir

# 3. Configure isolated test database (defaults to docmind_test_db or isolated test database session)
test_db_path = os.path.join(tmp_test_dir, "isolated_test_docmind.db")
test_db_url = os.getenv("TEST_DATABASE_URL", f"sqlite:///{test_db_path}")
os.environ["DATABASE_URL"] = test_db_url

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DatabaseManager
from backend.core.config import settings

# Update settings paths dynamically for test process
settings.DOCUMENTS_DIR = test_docs_dir
settings.VECTOR_DIR = test_vecs_dir

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    DatabaseManager.init_db()
    yield
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass
