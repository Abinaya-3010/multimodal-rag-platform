from fastapi import FastAPI
from app.core.config import get_settings
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="0.1.0",
    description="Multi-tenant multimodal RAG platform",
)

# Register routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.app_env,
    }