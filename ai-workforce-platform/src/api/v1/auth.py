import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.deps import get_db, get_current_user
from src.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenData
from src.services.auth import hash_password, verify_password, create_access_token
from src.models.user import User
from src.models.company import Company

router = APIRouter(prefix="/auth", tags=["auth"])


async def register_user(db: AsyncSession, email: str, password: str, company_name: str) -> User:
    company = Company(name=company_name)
    db.add(company)
    await db.flush()

    user = User(
        company_id=company.id,
        email=email,
        role="admin",
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


@router.post("/register", response_model=TokenResponse)
async def register(body: UserRegister, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = await register_user(db, body.email, body.password, body.company_name)
    token = create_access_token(str(user.id), str(user.company_id), user.role)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await authenticate_user(db, body.email, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user.id), str(user.company_id), user.role)
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(current_user: TokenData = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "company_id": current_user.company_id,
        "role": current_user.role,
    }
