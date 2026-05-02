from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    status: str
    version: str = "0.1.0"


@router.get("/", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Detailed health check endpoint."""
    return HealthResponse(status="ok")
