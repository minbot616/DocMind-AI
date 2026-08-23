import os
import sys
import shutil
from typing import List, Optional
from backend.core.config import settings

# Ensure root workspace modules are importable
if settings.BASE_DIR not in sys.path:
    sys.path.insert(0, settings.BASE_DIR)

from database import DatabaseManager
from document_processor import DocumentProcessor
from embeddings import EmbeddingManager
from vector_store import VectorStoreManager
from utils import allowed_file, get_file_extension
from backend.schemas.documents import DocumentResponse, DocumentListResponse

class DocumentService:

    @staticmethod
    def list_documents(user_id: int = 1) -> DocumentListResponse:
        docs = DatabaseManager.get_documents(user_id)
        doc_models = [DocumentResponse(**doc) for doc in docs]
        return DocumentListResponse(documents=doc_models, total=len(doc_models))

    @staticmethod
    def get_document(document_id: int) -> Optional[DocumentResponse]:
        doc = DatabaseManager.get_document(document_id)
        if doc:
            return DocumentResponse(**doc)
        return None

    @staticmethod
    def upload_document(user_id: int, filename: str, content: bytes) -> DocumentResponse:
        user_docs_dir = os.path.join(settings.DOCUMENTS_DIR, str(user_id))
        os.makedirs(user_docs_dir, exist_ok=True)

        if not allowed_file(filename):
            raise ValueError(f"Unsupported file format: {filename}")

        # Unique file naming on collision
        dest_path = os.path.join(user_docs_dir, filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(dest_path):
            filename = f"{base}_{counter}{ext}"
            dest_path = os.path.join(user_docs_dir, filename)
            counter += 1

        with open(dest_path, "wb") as f:
            f.write(content)

        file_size = len(content)
        file_type = get_file_extension(filename).replace(".", "").upper()

        # 1. Add document record
        doc_id = DatabaseManager.add_document(
            user_id=user_id,
            filename=filename,
            file_path=dest_path,
            file_type=file_type,
            file_size=file_size
        )

        # 2. Get Settings
        user_settings = DatabaseManager.get_settings(user_id)
        embed_name = user_settings.get("embedding_model", settings.DEFAULT_EMBEDDING_MODEL)
        api_key = user_settings.get("api_key", "")
        chunk_size = user_settings.get("chunk_size", settings.DEFAULT_CHUNK_SIZE)
        chunk_overlap = user_settings.get("chunk_overlap", settings.DEFAULT_CHUNK_OVERLAP)

        # 3. Process & Chunk
        pages = DocumentProcessor.process_document(dest_path)
        chunks = DocumentProcessor.chunk_documents(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap, document_id=doc_id)
        DatabaseManager.update_document_stats(doc_id, len(pages), len(chunks))


        # 4. Create Vector Store
        embed_model = EmbeddingManager.get_embeddings(embed_name, api_key)
        VectorStoreManager.create_vector_store(
            user_id=user_id,
            doc_id=doc_id,
            chunks=chunks,
            embedding_model=embed_model
        )

        doc_dict = DatabaseManager.get_document(doc_id)
        return DocumentResponse(**doc_dict)

    @staticmethod
    def delete_document(document_id: int) -> bool:
        doc = DatabaseManager.get_document(document_id)
        if not doc:
            return False

        user_id = doc["user_id"]
        # Delete Vector Store
        VectorStoreManager.delete_vector_store(user_id, document_id)

        # Delete File
        if os.path.exists(doc["file_path"]):
            try:
                os.remove(doc["file_path"])
            except Exception:
                pass

        # Delete DB Record
        return DatabaseManager.delete_document(document_id)

document_service = DocumentService()
