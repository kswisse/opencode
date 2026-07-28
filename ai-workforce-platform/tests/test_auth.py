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