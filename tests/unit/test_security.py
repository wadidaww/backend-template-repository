from __future__ import annotations

from datetime import timedelta

import pytest

from app.common.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
)


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


class TestPasswordEdgeCases:
    def test_long_password_round_trips(self):
        long_password = "pässwörd-" * 20  # > 72 bytes
        hashed = get_password_hash(long_password, rounds=4)
        assert verify_password(long_password, hashed)
        assert not verify_password(long_password[:-1], hashed)

    def test_long_passwords_sharing_prefix_differ(self):
        base = "a" * 80
        hashed = get_password_hash(base + "1", rounds=4)
        assert not verify_password(base + "2", hashed)

    def test_malformed_hash_returns_false(self):
        assert verify_password("anything", "not-a-bcrypt-hash") is False


class TestTokenEdgeCases:
    def test_expired_token_raises(self):
        token = create_access_token({"sub": "u1"}, expires_delta=timedelta(seconds=-1))
        with pytest.raises(UnauthorizedError, match="expired"):
            verify_token(token)

    def test_token_without_subject_raises(self):
        token = create_access_token({}, expires_delta=timedelta(minutes=1))
        with pytest.raises(UnauthorizedError):
            verify_token(token)

    def test_token_signed_with_other_key_raises(self):
        import jwt

        forged = jwt.encode(
            {"sub": "u1", "exp": 9999999999}, "another-key-" * 4, algorithm="HS256"
        )
        with pytest.raises(UnauthorizedError):
            verify_token(forged)
