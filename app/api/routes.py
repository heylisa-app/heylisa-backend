from fastapi import APIRouter, Depends
from asyncpg.pool import Pool

from app.db.pool import get_pool
from app.services.quota import get_quota_status

router = APIRouter()


@router.get("/health")
async def health(pool: Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        v = await conn.fetchval("select 1")
    return {"ok": True, "db": v}


@router.get("/v1/quota/{public_user_id}")
async def quota(public_user_id: str, pool: Pool = Depends(get_pool)):
    async with pool.acquire() as conn:
        status = await get_quota_status(conn, public_user_id)

    return {
        "public_user_id": public_user_id,
        "is_pro": status.is_pro,
        "free_quota_used": status.used,
        "free_quota_limit": status.limit,
        "state": status.state,  # normal | warn_last_free | blocked
        "paywall_should_show": (not status.is_pro) and (status.used >= status.limit),
    }