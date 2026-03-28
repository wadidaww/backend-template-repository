from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.exceptions.base import UnauthorizedError


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = get_password_hash("mysecretpassword")
        assert isinstance(hashed, str)
        assert hashed != "mysecretpassword"

    def test_verify_correct_password(self):
        password = "mysecretpassword"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_produces_different_hashes(self):
        password = "samepassword"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        assert hash1 != hash2


class TestJWTTokens:
    def test_create_access_token(self):
        token = create_access_token({"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_access_token(self):
        token = create_access_token({"sub": "user-123"})
        payload = verify_token(token)
        assert payload.sub == "user-123"
        assert payload.token_type == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "user-123"})
        payload = verify_token(token)
        assert payload.sub == "user-123"
        assert payload.token_type == "refresh"

    def test_token_with_custom_expiry(self):
        token = create_access_token(
            {"sub": "user-456"}, expires_delta=timedelta(minutes=5)
        )
        payload = verify_token(token)
        assert payload.sub == "user-456"

    def test_verify_invalid_token_raises(self):
        with pytest.raises(UnauthorizedError):
            verify_token("this.is.invalid")

    def test_verify_tampered_token_raises(self):
        token = create_access_token({"sub": "user-123"})
        tampered = token[:-5] + "xxxxx"
        with pytest.raises(UnauthorizedError):
            verify_token(tampered)
