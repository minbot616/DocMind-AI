from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from typing import Optional, List, Dict, Any
import os

from backend.api.dependencies import get_current_user_id
from backend.schemas.documents import DocumentResponse, DocumentListResponse
from backend.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["Documents"])

def _get_doc_user_id(doc):
    if isinstance(doc, dict):
        return doc.get("user_id")
    return getattr(doc, "user_id", None)

@router.get("", response_model=DocumentListResponse)
def list_documents(user_id: int = Depends(get_current_user_id)):
    """List all documents uploaded by the current user."""
    return document_service.list_documents(user_id=user_id)

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Retrieve metadata for a single document."""
    doc = document_service.get_document(document_id)
    if not doc or _get_doc_user_id(doc) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found."
        )
    return doc

@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    """Upload a single document with filename sanitization, type validation, and size limits."""
    clean_filename = os.path.basename(file.filename or "uploaded_document")
    ext = os.path.splitext(clean_filename)[1].lower()
    if ext not in [".pdf", ".txt", ".docx", ".md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only PDF, TXT, DOCX, and MD are supported."
        )

    try:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum allowed limit of 50MB."
            )

        return document_service.upload_document(
            user_id=user_id,
            filename=clean_filename,
            content=content
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process document: {str(e)}")

@router.post("/upload-multiple", status_code=status.HTTP_200_OK)
@router.post("/upload-batch", status_code=status.HTTP_200_OK)
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    user_id: int = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """Upload multiple documents in one batch operation, returning per-file success/failure results."""
    uploaded = []
    failed = []

    for file in files:
        clean_filename = os.path.basename(file.filename or "uploaded_document")
        ext = os.path.splitext(clean_filename)[1].lower()
        if ext not in [".pdf", ".txt", ".docx", ".md"]:
            failed.append({
                "filename": clean_filename,
                "status": "rejected",
                "reason": f"Unsupported file format '{ext}'. Only PDF, TXT, DOCX, and MD are supported."
            })
            continue

        try:
            content = await file.read()
            if len(content) > 50 * 1024 * 1024:
                failed.append({
                    "filename": clean_filename,
                    "status": "rejected",
                    "reason": "File size exceeds maximum allowed limit of 50MB."
                })
                continue

            doc_resp = document_service.upload_document(
                user_id=user_id,
                filename=clean_filename,
                content=content
            )
            if isinstance(doc_resp, dict):
                doc_dict = doc_resp
            elif hasattr(doc_resp, "model_dump"):
                doc_dict = doc_resp.model_dump()
            else:
                doc_dict = doc_resp.dict()

            uploaded.append(doc_dict)
        except Exception as e:
            failed.append({
                "filename": clean_filename,
                "status": "rejected",
                "reason": str(e)
            })

    return {"uploaded": uploaded, "failed": failed}

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    user_id: int = Depends(get_current_user_id)
):
    """Delete a document record, file, and vector store."""
    doc = document_service.get_document(document_id)
    if not doc or _get_doc_user_id(doc) != user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found or could not be deleted."
        )

    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found or could not be deleted."
        )
    return None
