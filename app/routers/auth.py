from datetime import timedelta
from typing import Annotated
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.core import SessionDep, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas import Token
from app.utils import authenticate_user
from app.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep
) -> Token:
    user: User | None = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.email), "id": user.id}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
