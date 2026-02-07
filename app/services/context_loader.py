# app/services/context_loader.py
from __future__ import annotations

from asyncpg import Connection


async def load_context_light(conn: Connection, public_user_id: str, conversation_id: str) -> dict:
    # 1) user identity
    user = await conn.fetchrow(
        """
        select id, first_name, last_name, full_name
        from public.users
        where id = $1
        """,
        public_user_id,
    )

    # 2) settings (defaults if missing)
    settings_row = await conn.fetchrow(
        """
        select
            coalesce(locale_main, 'fr-FR') as locale_main,
            coalesce(timezone, 'UTC') as timezone,
            coalesce(use_tu_form, false) as use_tu_form,
            coalesce(intro_smalltalk_turns, 0) as intro_smalltalk_turns,
            coalesce(intro_smalltalk_done, false) as intro_smalltalk_done,
            coalesce(free_quota_limit, 8) as free_quota_limit,
            coalesce(free_quota_used, 0) as free_quota_used
        from public.user_settings
        where user_id = $1
        """,
        public_user_id,
    )

    if not settings_row:
        settings = {
            "locale_main": "fr-FR",
            "timezone": "UTC",
            "use_tu_form": False,
            "intro_smalltalk_turns": 0,
            "intro_smalltalk_done": False,
            "free_quota_limit": 8,
            "free_quota_used": 0,
        }
    else:
        settings = dict(settings_row)

    # 3) last messages (10) for this conversation
    rows = await conn.fetch(
        """
        select role, content, sent_at
        from public.conversation_messages
        where conversation_id = $1
        order by sent_at desc, id desc
        limit 10
        """,
        conversation_id,
    )

    # we fetched DESC => reverse to get chronological order
    rows = list(reversed(rows))

    messages = [
        {
            "role": "assistant" if r["role"] == "assistant" else "user",
            "content": r["content"],
        }
        for r in rows
    ]

    return {
        "user": dict(user) if user else None,
        "settings": settings,
        "messages": messages,
    }