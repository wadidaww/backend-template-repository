import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

_bearer_scheme = HTTPBearer()

# Simple in-memory JWKS cache to avoid fetching on every request.
_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.auth0_jwks_uri)
            response.raise_for_status()
            _jwks_cache = response.json()
    return _jwks_cache


def _credentials_exception(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """FastAPI dependency that validates an Auth0 JWT and returns its payload."""
    token = credentials.credentials

    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError as exc:
        raise _credentials_exception("Invalid token header") from exc

    jwks = await _get_jwks()
    rsa_key: dict = {}
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break

    if not rsa_key:
        raise _credentials_exception("Unable to find a suitable signing key")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )
    except JWTError as exc:
        raise _credentials_exception(f"Token validation failed: {exc}") from exc

    return payload
