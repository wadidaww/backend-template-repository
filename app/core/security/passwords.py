"""Password hashing with bcrypt.

bcrypt only looks at the first 72 bytes of a password and raises on longer
input (bcrypt>=4.1), so passwords are pre-hashed with SHA-256 when they exceed
that length. This keeps long passphrases working without silently truncating.
"""

from __future__ import annotations

import base64
import hashlib

import bcrypt

_BCRYPT_MAX_BYTES = 72


def _prepare(password: str) -> bytes:
    raw = password.encode("utf-8")
    if len(raw) > _BCRYPT_MAX_BYTES:
        raw = base64.b64encode(hashlib.sha256(raw).digest())
    return raw


def get_password_hash(password: str, *, rounds: int = 12) -> str:
    return bcrypt.hashpw(_prepare(password), bcrypt.gensalt(rounds=rounds)).decode(
        "ascii"
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(plain_password), hashed_password.encode("ascii"))
    except ValueError:
        # Malformed hash stored in the database.
        return False
