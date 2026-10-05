from src.config import settings

def test_config_has_jwt_settings():
    assert hasattr(settings, "jwt_secret_key")
    assert hasattr(settings, "jwt_algorithm")
    assert hasattr(settings, "jwt_expiry_minutes")
    assert settings.jwt_algorithm == "HS256"

def test_auth_dependencies_installed():
    import jose
    import passlib
    assert jose.__version__
    assert passlib.__version__

import uuid
from src.models.user import User

def test_user_model_has_required_fields():
    user = User(
        id=uuid.uuid4(),
        company_id=uuid.uuid4(),
        email="test@example.com",
        role="admin",
        hashed_password="hashed"
    )
    assert user.email == "test@example.com"
    assert user.role == "admin"

from src.schemas.auth import UserRegister, UserLogin, TokenResponse, TokenData

def test_auth_schemas_validation():
    reg = UserRegister(email="a@b.com", password="secret123", company_name="Acme")
    assert reg.email == "a@b.com"

    login = UserLogin(email="a@b.com", password="secret123")
    assert login.email == "a@b.com"

    token = TokenResponse(access_token="abc", token_type="bearer")
    assert token.token_type == "bearer"

    data = TokenData(user_id="123", company_id="456", role="admin")
    assert data.role == "admin"

from src.services.auth import hash_password, verify_password, create_access_token, decode_access_token

def test_password_hashing():
    pwd = "mypassword"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed)
    assert not verify_password("wrong", hashed)

def test_jwt_create_decode():
    token = create_access_token("user123", "company456", "admin")
    data = decode_access_token(token)
    assert data.user_id == "user123"
    assert data.company_id == "company456"
    assert data.role == "admin"

def test_jwt_invalid_token():
    result = decode_access_token("invalid.token.here")
    assert result is None

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from src.api.deps import get_current_user

@pytest.mark.asyncio
async def test_get_current_user_valid():
    from unittest.mock import MagicMock
    token = create_access_token("user1", "company1", "admin")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    mock_request = MagicMock()
    result = await get_current_user(mock_request, creds)
    assert result.user_id == "user1"
    assert result.company_id == "company1"
    assert result.role == "admin"

@pytest.mark.asyncio
async def test_get_current_user_invalid():
    from unittest.mock import MagicMock
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid.token")
    mock_request = MagicMock()
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_request, creds)
    assert exc_info.value.status_code == 401

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from src.main import create_app
from src.database import get_db

@pytest.fixture
def auth_client():
    app = create_app()
    async def override_get_db():
        db = AsyncMock(spec=MagicMock)
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        db.rollback = AsyncMock()
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        db.execute = AsyncMock(return_value=mock_result)
        yield db
    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.mark.asyncio
async def test_me_requires_auth(auth_client):
    transport = ASGITransport(app=auth_client)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

@pytest.mark.asyncio
async def test_me_with_valid_token(auth_client):
    token = create_access_token("user1", "company1", "admin")
    transport = ASGITransport(app=auth_client)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user1"
        assert data["company_id"] == "company1"
        assert data["role"] == "admin"