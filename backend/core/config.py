import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Settings:
    APP_NAME: str = "DocMind AI API"
    APP_VERSION: str = "1.0.0"
    ENV: str = os.getenv("DOCMIND_ENV", "development")

    # Paths
    BASE_DIR: str = BASE_DIR
    DATABASE_DIR: str = os.path.join(BASE_DIR, "database")
    USERS_DB: str = os.path.join(DATABASE_DIR, "users.db")
    HISTORY_DB: str = os.path.join(DATABASE_DIR, "history.db")
    DOCUMENTS_DIR: str = os.getenv("DOCMIND_DOCUMENTS_DIR", os.path.join(BASE_DIR, "documents"))
    VECTOR_DIR: str = os.getenv("DOCMIND_VECTOR_DIR", os.path.join(BASE_DIR, "vectors"))


    # Defaults
    DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    DEFAULT_LLM_PROVIDER: str = "Ollama"
    DEFAULT_LLM_MODEL: str = "llama3"
    DEFAULT_CHUNK_SIZE: int = 500
    DEFAULT_CHUNK_OVERLAP: int = 50
    DEFAULT_TEMPERATURE: float = 0.2
    DEFAULT_MAX_TOKENS: int = 1024

settings = Settings()
