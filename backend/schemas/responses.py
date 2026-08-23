from pydantic import BaseModel
from typing import Optional, Any

class HealthResponse(BaseModel):
    status: str = "ok"

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail
