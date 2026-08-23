from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field
from repositories.user_repository import UserRepository
from backend.core.security import create_access_token
from backend.api.dependencies import get_current_user_id

router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

@router.post("/register")
def register_user(req: RegisterRequest):
    success, msg = UserRepository.register_user(req.username, req.password)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)
    user = UserRepository.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User creation verification failed.")
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login")
def login_user(req: LoginRequest):
    user = UserRepository.authenticate_user(req.username, req.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password.")
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
def get_current_user_info(user_id: int = Depends(get_current_user_id)):
    from backend.database.config import get_db_session
    from backend.database.models import UserModel
    with get_db_session() as session:
        user = session.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return {"id": user.id, "username": user.username, "created_at": user.created_at.isoformat()}

