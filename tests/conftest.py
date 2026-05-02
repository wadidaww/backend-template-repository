"""Shared test fixtures."""
import json
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from jose import jwt

# ---------------------------------------------------------------------------
# Generate a temporary RSA key pair used for signing test tokens
# ---------------------------------------------------------------------------
_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_public_key = _private_key.public_key()

TEST_DOMAIN = "test.auth0.com"
TEST_AUDIENCE = "https://test-api/"
TEST_ISSUER = f"https://{TEST_DOMAIN}/"
TEST_KID = "test-key-id"
TEST_SUB = "auth0|testuser123"

# Build a minimal JWKS from the generated public key.
_pub_numbers = _public_key.public_key().public_numbers() if hasattr(_public_key, "public_key") else _public_key.public_numbers()

import base64, math


def _int_to_base64url(n: int) -> str:
    byte_length = (n.bit_length() + 7) // 8
    return base64.urlsafe_b64encode(n.to_bytes(byte_length, "big")).rstrip(b"=").decode()


FAKE_JWKS = {
    "keys": [
        {
            "kty": "RSA",
            "kid": TEST_KID,
            "use": "sig",
            "n": _int_to_base64url(_pub_numbers.n),
            "e": _int_to_base64url(_pub_numbers.e),
        }
    ]
}


def make_token(sub: str = TEST_SUB, audience: str = TEST_AUDIENCE, issuer: str = TEST_ISSUER) -> str:
    """Create a signed JWT using the test private key."""
    private_pem = _private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    )
    return jwt.encode(
        {"sub": sub, "iss": issuer, "aud": audience},
        private_pem,
        algorithm="RS256",
        headers={"kid": TEST_KID},
    )


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    """Override settings so no real .env file is required."""
    monkeypatch.setenv("AUTH0_DOMAIN", TEST_DOMAIN)
    monkeypatch.setenv("AUTH0_AUDIENCE", TEST_AUDIENCE)

    # Re-create the settings object with the patched env.
    from app import config
    monkeypatch.setattr(config, "settings", config.Settings())

    # Also patch the settings reference inside auth module.
    import app.auth as auth_module
    monkeypatch.setattr(auth_module, "settings", config.settings)


@pytest.fixture(autouse=True)
def reset_jwks_cache():
    """Clear the JWKS cache before each test."""
    import app.auth as auth_module
    auth_module._jwks_cache = None
    yield
    auth_module._jwks_cache = None


@pytest.fixture
def mock_jwks():
    """Patch the JWKS fetch to return the fake JWKS."""
    with patch("app.auth._get_jwks", new_callable=AsyncMock, return_value=FAKE_JWKS):
        yield


@pytest.fixture
def client(mock_jwks):
    from app.main import app
    return TestClient(app)
