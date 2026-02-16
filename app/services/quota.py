from dataclasses import dataclass
from typing import Literal
from asyncpg import Connection

QuotaState = Literal["normal", "warn_last_free", "blocked"]

@dataclass
class QuotaStatus:
    is_pro: bool
    used: int
    limit: int
    state: QuotaState

async def get_quota_status(conn: Connection, public_user_id: str) -> QuotaStatus:
    row = await conn.fetchrow(
        """
        select
          coalesce(u.is_pro, false) as is_pro,
          coalesce(us.free_quota_used, 0) as used,
          coalesce(us.free_quota_limit, 8) as "limit"
        from public.users u
        left join public.user_settings us on us.user_id = u.id
        where u.id = $1
        """,
        public_user_id,
    )

    if row is None:
        # On fail-closed côté backend: si user inconnu -> blocked
        return QuotaStatus(is_pro=False, used=9999, limit=8, state="blocked")

    is_pro = bool(row["is_pro"])
    used = int(row["used"])
    limit = int(row["limit"])

    if is_pro:
        return QuotaStatus(is_pro=True, used=used, limit=limit, state="normal")

    # Invariant: jamais de reset quota
    # warn au message #7 (i.e. used == limit - 1)
    if used >= limit:
        state: QuotaState = "blocked"
    elif used == (limit - 1):
        state = "warn_last_free"
    else:
        state = "normal"

    return QuotaStatus(is_pro=False, used=used, limit=limit, state=state)