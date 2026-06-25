from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from app.config import settings
from app.utils.security import create_access_token, verify_password, get_password_hash
from app.api import deps
from app.models.user import User, UserCreate, Token, UserInDB
from app.repositories.user import UserRepository
from typing import Any

router = APIRouter()

@router.post("/register", response_model=User)
async def register(
    user_in: UserCreate,
    user_repo: UserRepository = Depends(deps.get_user_repository)
) -> Any:
    user = await user_repo.get_by_email(user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    hashed_password = get_password_hash(user_in.password)
    new_user = await user_repo.create(user_in, hashed_password)
    return new_user

@router.post("/login", response_model=Token)
async def login(
    user_repo: UserRepository = Depends(deps.get_user_repository),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.get("/me", response_model=User)
async def get_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    return current_user
