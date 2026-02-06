# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.logging import setup_logging, logger
from app.db.pool import init_pool, close_pool
from app.settings import settings

# Logging setup (once at import time)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_pool()
    logger.info(
        "heylisa_backend_started",
        environment=settings.environment,
        service="heylisa-backend",
    )
    yield
    # Shutdown
    await close_pool()
    logger.info("heylisa_backend_stopped", service="heylisa-backend")


app = FastAPI(
    title="HeyLisa Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Routers
app.include_router(router)


# Root endpoint (quick smoke test)
@app.get("/")
async def root():
    logger.info("root_endpoint_called")
    return {"status": "ok", "service": "heylisa-backend"}