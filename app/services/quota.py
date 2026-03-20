# app/services/quota.py
from __future__ import annotations

from dataclasses import dataclass
from asyncpg import Connection


@dataclass
class QuotaStatus:
    is_pro: bool
    used: int
    limit: int
    state: str  # normal | warn_last_free | blocked


async def get_quota_status(conn: Connection, public_user_id: str) -> QuotaStatus:
    """
    Version minimaliste temporaire, découplée de l'ancien schéma.
    On neutralise la logique abonnement/quota pour remettre le chat en route.
    """

    return QuotaStatus(
        is_pro=False,
        used=0,
        limit=999,
        state="normal",
    )