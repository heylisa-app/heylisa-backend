# app/tools/onboarding_update.py
from __future__ import annotations

from typing import Any, Dict, Optional, List
from asyncpg import Connection


async def onboarding_update(
    conn: Connection,
    *,
    user_id: str,
    agent_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Autonomous onboarding completion tool.

    Behavior:
    - Scan agents with onboarding_status = "started"
    - If user has interacted at least once (message role='user')
      => set onboarding_status = "complete"
    - Never downgrade
    - Idempotent
    """

    # 1️⃣ Récupérer agents started
    if agent_key:
        rows = await conn.fetch(
            """
            select agent_key, onboarding_status
            from public.lisa_user_agents
            where user_id = $1
              and agent_key = $2
              and onboarding_status = 'started'
            """,
            user_id,
            agent_key,
        )
    else:
        rows = await conn.fetch(
            """
            select agent_key, onboarding_status
            from public.lisa_user_agents
            where user_id = $1
              and onboarding_status = 'started'
            """,
            user_id,
        )

    if not rows:
        return {
            "ok": True,
            "updated": [],
            "reason": "NO_STARTED_AGENTS",
        }

    # 2️⃣ Vérifier interaction user
    user_msg = await conn.fetchrow(
        """
        select id
        from public.conversation_messages
        where user_id = $1
          and role = 'user'
        order by created_at desc
        limit 1
        """,
        user_id,
    )

    if not user_msg:
        return {
            "ok": True,
            "updated": [],
            "reason": "NO_USER_ACTIVITY",
        }

    updated: List[str] = []

    # 3️⃣ Update agents
    for r in rows:
        ak = r["agent_key"]

        await conn.execute(
            """
            update public.lisa_user_agents
            set onboarding_status = 'complete'
            where user_id = $1
              and agent_key = $2
              and onboarding_status = 'started'
            """,
            user_id,
            ak,
        )

        updated.append(ak)

    return {
        "ok": True,
        "updated": updated,
        "reason": "USER_ACTIVITY_DETECTED",
    }