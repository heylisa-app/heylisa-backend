import asyncpg
from asyncpg import Pool
from app.settings import settings

_pool: Pool | None = None

async def init_pool() -> Pool:
    global _pool
    if _pool is not None:
        return _pool

    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=1,
        max_size=10,
        command_timeout=10,
    )
    return _pool

async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None

async def get_pool() -> Pool:
    if _pool is None:
        return await init_pool()
    return _pool