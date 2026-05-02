from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/api/public")
async def public_endpoint() -> dict:
    return {"message": "This endpoint is publicly accessible."}
