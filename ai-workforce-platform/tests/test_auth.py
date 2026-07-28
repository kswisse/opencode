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