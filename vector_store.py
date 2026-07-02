import os
import shutil
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

VECTOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectors")
os.makedirs(VECTOR_DIR, exist_ok=True)

class VectorStoreManager:
    """Manages creation, serialization, deletion, and merging of FAISS vector databases."""

    @staticmethod
    def get_store_path(user_id: int, doc_id: int) -> str:
        """Gets the path where a document's vector store is saved."""
        path = os.path.join(VECTOR_DIR, str(user_id), f"doc_{doc_id}")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def create_vector_store(cls, user_id: int, doc_id: int, chunks: List[Dict[str, Any]], embedding_model: Any) -> str:
        """Creates a FAISS vector store from text chunks and saves it to disk.
        
        Args:
            user_id: ID of the user owning the document.
            doc_id: ID of the document metadata entry.
            chunks: A list of dicts with 'text' and 'metadata'.
            embedding_model: The active embedding model instance.
        """
        # Convert chunk dictionaries to LangChain Document objects
        documents = [
            Document(page_content=chunk["text"], metadata=chunk["metadata"])
            for chunk in chunks
        ]
        
        # Create and save FAISS index
        vector_store = FAISS.from_documents(documents, embedding_model)
        store_path = cls.get_store_path(user_id, doc_id)
        
        # Ensure directory is empty/exists
        if os.path.exists(store_path):
            shutil.rmtree(store_path, ignore_errors=True)
            
        vector_store.save_local(store_path)
        return store_path

    @classmethod
    def load_vector_store(cls, user_id: int, doc_id: int, embedding_model: Any) -> Optional[FAISS]:
        """Loads a document's vector store from disk."""
        store_path = cls.get_store_path(user_id, doc_id)
        if not os.path.exists(os.path.join(store_path, "index.faiss")):
            return None
        
        # allow_dangerous_deserialization=True is required for loading pickled FAISS databases locally
        return FAISS.load_local(store_path, embedding_model, allow_dangerous_deserialization=True)

    @classmethod
    def load_merged_vector_store(cls, user_id: int, doc_ids: List[int], embedding_model: Any) -> Optional[FAISS]:
        """Loads and merges vector stores for multiple documents in memory.
        
        Args:
            user_id: ID of the user.
            doc_ids: List of document IDs to merge.
            embedding_model: Embedding model to use for the stores.
        """
        if not doc_ids:
            return None
        
        merged_store = None
        for doc_id in doc_ids:
            store = cls.load_vector_store(user_id, doc_id, embedding_model)
            if store:
                if merged_store is None:
                    merged_store = store
                else:
                    merged_store.merge_from(store)
                    
        return merged_store

    @classmethod
    def delete_vector_store(cls, user_id: int, doc_id: int) -> bool:
        """Deletes the vector store directory from disk."""
        store_path = cls.get_store_path(user_id, doc_id)
        if os.path.exists(store_path):
            try:
                shutil.rmtree(store_path)
                return True
            except Exception:
                return False
        return True
