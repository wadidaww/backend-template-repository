from fastapi import FastAPI

from app.routers import private, public

app = FastAPI(
    title="Backend Template",
    description="FastAPI backend with Auth0 authentication.",
    version="1.0.0",
)

app.include_router(public.router)
app.include_router(private.router)
