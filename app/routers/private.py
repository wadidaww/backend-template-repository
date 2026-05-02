from fastapi import APIRouter, Depends

from app.auth import verify_token

router = APIRouter()


@router.get("/api/private")
async def private_endpoint(token_payload: dict = Depends(verify_token)) -> dict:
    """Protected endpoint — requires a valid Auth0 access token."""
    return {
        "message": "This endpoint requires authentication.",
        "sub": token_payload.get("sub"),
    }
