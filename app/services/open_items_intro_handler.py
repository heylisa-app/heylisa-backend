#app/services/open_items_intro_handler.py

from __future__ import annotations

from asyncpg import Connection

from app.services.open_items_intro import build_open_items_intro, OpenItemsIntroError


class OpenItemsIntroHandlerError(Exception):
    pass


async def _get_public_user_id_from_auth(conn: Connection, auth_user_id: str) -> str | None:
    row = await conn.fetchrow(
        """
        select id
        from public.users
        where auth_user_id = $1
        limit 1
        """,
        auth_user_id,
    )
    return str(row["id"]) if row else None


async def _get_open_session(
    conn: Connection,
    *,
    session_id: str,
    public_user_id: str,
):
    return await conn.fetchrow(
        """
        select id, public_user_id, cabinet_id, priority_info_request_id, status
        from public.open_items_chat_sessions
        where id = $1::uuid
          and public_user_id = $2::uuid
          and status = 'open'
        limit 1
        """,
        session_id,
        public_user_id,
    )


async def _count_session_messages(conn: Connection, *, session_id: str) -> int:
    value = await conn.fetchval(
        """
        select count(*)
        from public.open_items_chat_messages
        where session_id = $1::uuid
        """,
        session_id,
    )
    return int(value or 0)


async def _insert_lisa_intro_message(
    conn: Connection,
    *,
    session_id: str,
    public_user_id: str,
    assistant_text: str,
) -> dict:
    dedupe_key = f"open_items:intro:{session_id}"

    row = await conn.fetchrow(
        """
        insert into public.open_items_chat_messages (
          session_id,
          sender_type,
          role,
          content,
          dedupe_key,
          metadata
        )
        values (
          $1::uuid,
          'lisa',
          'assistant',
          $2::text,
          $3::text,
          jsonb_build_object(
            'event_type', 'open_items_intro',
            'source', 'backend'
          )
        )
        on conflict (session_id, dedupe_key) do update
        set content = excluded.content,
            metadata = excluded.metadata
        returning id, content, sent_at, metadata
        """,
        session_id,
        assistant_text,
        dedupe_key,
    )

    return {
        "id": str(row["id"]),
        "content": str(row["content"] or ""),
        "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
        "metadata": row["metadata"] or {},
    }


async def handle_open_items_intro(
    conn: Connection,
    *,
    session_id: str,
    auth_user_id: str | None = None,
    public_user_id_override: str | None = None,
) -> dict:
    public_user_id = None

    if public_user_id_override:
        public_user_id = public_user_id_override
    elif auth_user_id:
        public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)

    if not public_user_id:
        raise OpenItemsIntroHandlerError("AUTH_USER_NOT_LINKED")

    session_row = await _get_open_session(
        conn,
        session_id=session_id,
        public_user_id=public_user_id,
    )
    if not session_row:
        raise OpenItemsIntroHandlerError("OPEN_ITEMS_SESSION_NOT_FOUND")

    messages_count = await _count_session_messages(conn, session_id=session_id)

    if messages_count > 0:
        return {
            "ok": True,
            "session_id": session_id,
            "already_initialized": True,
            "messages_count": messages_count,
            "assistant_message": None,
        }

    priority_info_request_id = (
        str(session_row["priority_info_request_id"])
        if session_row["priority_info_request_id"]
        else None
    )

    try:
        intro = await build_open_items_intro(
            conn,
            public_user_id=public_user_id,
            priority_info_request_id=priority_info_request_id,
        )
    except OpenItemsIntroError as e:
        raise OpenItemsIntroHandlerError(str(e))

    assistant_message = await _insert_lisa_intro_message(
        conn,
        session_id=session_id,
        public_user_id=public_user_id,
        assistant_text=intro["assistant_text"],
    )

    return {
        "ok": True,
        "session_id": session_id,
        "already_initialized": False,
        "messages_count": 1,
        "assistant_message": assistant_message,
    }