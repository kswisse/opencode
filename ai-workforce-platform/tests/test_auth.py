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