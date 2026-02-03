from datetime import datetime
from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
