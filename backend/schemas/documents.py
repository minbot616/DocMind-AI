from pydantic import BaseModel
from typing import List, Optional

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_path: str
    file_type: str
    file_size: int
    upload_time: str
    status: str = "processed"
    pages: int = 0
    chunks: int = 0

class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]
    total: int
