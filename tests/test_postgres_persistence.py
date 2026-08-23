import pytest
from backend.database.config import get_db_session, Base, engine
from database import DatabaseManager
from repositories.user_repository import UserRepository
from repositories.document_repository import DocumentRepository
from repositories.conversation_repository import ConversationRepository
from repositories.settings_repository import SettingsRepository
from scripts.migrate_sqlite_to_postgres import migrate

@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_user_repository_crud():
    success, msg = UserRepository.register_user("testuser_pg", "Secret123!")
    assert success is True
    assert "successful" in msg

    # Duplicate registration check
    dup_success, dup_msg = UserRepository.register_user("testuser_pg", "Secret123!")
    assert dup_success is False

    # Authentication
    user = UserRepository.authenticate_user("testuser_pg", "Secret123!")
    assert user is not None
    assert user["username"] == "testuser_pg"

    # Invalid password authentication
    bad_user = UserRepository.authenticate_user("testuser_pg", "WrongPass")
    assert bad_user is None

def test_document_repository_crud():
    doc_id = DocumentRepository.add_document(
        user_id=1,
        filename="test_architecture.pdf",
        file_path="/tmp/test_architecture.pdf",
        file_type="pdf",
        file_size=20480
    )
    assert doc_id > 0

    # Read
    doc = DocumentRepository.get_document(doc_id)
    assert doc is not None
    assert doc["filename"] == "test_architecture.pdf"

    # Update stats
    ok = DocumentRepository.update_document_stats(doc_id, pages=5, chunks=12)
    assert ok is True
    updated_doc = DocumentRepository.get_document(doc_id)
    assert updated_doc["pages"] == 5
    assert updated_doc["chunks"] == 12

    # Rename
    renamed = DocumentRepository.rename_document(doc_id, "architecture_v2.pdf")
    assert renamed is True

    # Search
    found = DocumentRepository.search_documents_by_name(1, "v2")
    assert len(found) >= 1

    # Delete
    deleted = DocumentRepository.delete_document(doc_id)
    assert deleted is True
    assert DocumentRepository.get_document(doc_id) is None

def test_conversation_and_messages_repository():
    chat_id = ConversationRepository.create_chat(user_id=1, title="PostgreSQL Test Chat")
    assert chat_id > 0

    # Add messages
    m1 = ConversationRepository.add_message(chat_id, "user", "What is FAISS?")
    m2 = ConversationRepository.add_message(
        chat_id,
        "assistant",
        "FAISS is a vector index.",
        sources=[{"document": "arch.pdf", "page": 1, "valid": True}]
    )
    assert m1 > 0
    assert m2 > 0

    # Retrieve messages
    messages = ConversationRepository.get_messages(chat_id)
    assert len(messages) == 2
    assert messages[1]["sources"][0]["document"] == "arch.pdf"

    # Summary persistence
    ConversationRepository.update_chat_summary(chat_id, "Discussion about FAISS vector indexing.")
    summary = ConversationRepository.get_chat_summary(chat_id)
    assert summary == "Discussion about FAISS vector indexing."

    # Cascade deletion check
    del_ok = ConversationRepository.delete_chat(chat_id)
    assert del_ok is True
    assert len(ConversationRepository.get_messages(chat_id)) == 0

def test_settings_repository():
    settings = SettingsRepository.get_settings(user_id=999)
    assert settings["theme"] == "Dark"
    assert settings["chunk_size"] == 500

    settings["theme"] = "Light"
    settings["chunk_size"] = 1000
    updated = SettingsRepository.update_settings(999, settings)
    assert updated is True

    new_settings = SettingsRepository.get_settings(user_id=999)
    assert new_settings["theme"] == "Light"
    assert new_settings["chunk_size"] == 1000

def test_sqlite_migration_script():
    migrate()

def test_postgres_failure_no_sqlite_fallback(monkeypatch, tmp_path):
    from backend.database import config
    # Set invalid PostgreSQL URL in environment variable
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@127.0.0.1:54399/docmind_invalid_test_db")


    with pytest.raises(RuntimeError) as exc_info:
        config.get_engine()

    assert "PostgreSQL database is unavailable" in str(exc_info.value)

    # Assert fallback db file is NOT created
    fallback_path = tmp_path / "docmind_pg_fallback.db"
    assert not fallback_path.exists()


