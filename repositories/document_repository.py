from typing import List, Dict, Any, Optional
from backend.database.config import get_db_session
from backend.database.models import DocumentModel
from utils import logger

class DocumentRepository:
    """Repository managing document library metadata."""

    @classmethod
    def add_document(cls, user_id: int, filename: str, file_path: str, file_type: str, file_size: int) -> int:
        with get_db_session() as session:
            doc = DocumentModel(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                status="processed"
            )
            session.add(doc)
            session.flush()
            doc_id = doc.id
        return doc_id

    @classmethod
    def update_document_stats(cls, doc_id: int, pages: int, chunks: int) -> bool:
        try:
            with get_db_session() as session:
                doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
                if doc:
                    doc.pages = pages
                    doc.chunks = chunks
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to update stats for doc_id {doc_id}")
            return False

    @classmethod
    def get_documents(cls, user_id: int) -> List[Dict[str, Any]]:
        with get_db_session() as session:
            docs = session.query(DocumentModel).filter(DocumentModel.user_id == user_id).order_by(DocumentModel.upload_time.desc()).all()
            return [doc.to_dict() for doc in docs]

    @classmethod
    def get_document(cls, doc_id: int) -> Optional[Dict[str, Any]]:
        with get_db_session() as session:
            doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            return doc.to_dict() if doc else None

    @classmethod
    def rename_document(cls, doc_id: int, new_name: str) -> bool:
        try:
            with get_db_session() as session:
                doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
                if doc:
                    doc.filename = new_name
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to rename document {doc_id} to '{new_name}'")
            return False

    @classmethod
    def delete_document(cls, doc_id: int) -> bool:
        try:
            with get_db_session() as session:
                doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
                if doc:
                    session.delete(doc)
                    return True
            return False
        except Exception:
            logger.exception(f"Failed to delete document metadata for doc_id {doc_id}")
            return False

    @classmethod
    def search_documents_by_name(cls, user_id: int, query: str) -> List[Dict[str, Any]]:
        try:
            with get_db_session() as session:
                pattern = f"%{query}%"
                docs = session.query(DocumentModel).filter(
                    DocumentModel.user_id == user_id,
                    DocumentModel.filename.ilike(pattern)
                ).order_by(DocumentModel.upload_time.desc()).all()
                return [doc.to_dict() for doc in docs]
        except Exception:
            logger.exception(f"Failed to search documents for user {user_id} with query '{query}'")
            return []
