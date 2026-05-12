from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserPrivateOut
from app.services.auth import register_user, authenticate_user, create_access_token, create_refresh_token

router = APIRouter()


@router.post("/register", response_model=UserPrivateOut, status_code=201)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await register_user(db, payload)
    return user


@router.post("/login", response_model=Token)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, form.username, form.password)
    return Token(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )