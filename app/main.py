from fastapi import FastAPI

from app.api.health import router as health_router
from app.core.config import settings
from app.core.logging import setup_logging, logger

setup_logging()

app = FastAPI(
    title="HeyLisa Backend",
    version="0.1.0",
)

app.include_router(health_router)


@app.on_event("startup")
async def startup_event():
    logger.info("heylisa_backend_started", environment=settings.environment)


@app.get("/")
async def root():
    logger.info("root_endpoint_called")
    return {"status": "ok", "service": "heylisa-backend"}
