# app/main.py
from dotenv import load_dotenv
load_dotenv()
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import setup_logging
import structlog

from app.api.routes import router
from app.db.pool import init_pool, close_pool
from app.settings import settings



# --- Logging setup (ONCE, at import time) ---
setup_logging()
logger = structlog.get_logger("app.main")
logger.info("logging_configured")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    logger.info(
        "heylisa_backend_started",
        environment=settings.environment,
        service="heylisa-backend",
    )
    yield
    await close_pool()
    logger.info("heylisa_backend_stopped", service="heylisa-backend")


app = FastAPI(
    title="HeyLisa Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/")
async def root():
    logger.info("root_endpoint_called")
    return {"status": "ok", "service": "heylisa-backend"}