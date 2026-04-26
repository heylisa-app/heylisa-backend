#app/services/open_items_session.py

from __future__ import annotations

from typing import Optional

from asyncpg import Connection


class OpenItemsSessionError(Exception):
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


async def _get_cabinet_id_for_user(conn: Connection, public_user_id: str) -> str | None:
    row = await conn.fetchrow(
        """
        select cabinet_account_id
        from public.cabinet_members
        where user_id = $1::uuid
          and status = 'active'
        order by created_at asc
        limit 1
        """,
        public_user_id,
    )
    if not row:
        return None
    return str(row["cabinet_account_id"]) if row["cabinet_account_id"] else None


async def _priority_item_belongs_to_cabinet(
    conn: Connection,
    *,
    cabinet_id: str,
    priority_info_request_id: Optional[str],
) -> bool:
    if not priority_info_request_id:
        return True

    row = await conn.fetchrow(
        """
        select id
        from public.cabinet_info_requests
        where id = $1::uuid
          and cabinet_id = $2::uuid
        limit 1
        """,
        priority_info_request_id,
        cabinet_id,
    )
    return bool(row)


async def get_or_create_open_items_session(
    conn: Connection,
    *,
    auth_user_id: Optional[str] = None,
    public_user_id_override: Optional[str] = None,
    priority_info_request_id: Optional[str] = None,
) -> dict:
    public_user_id = None

    if public_user_id_override:
        public_user_id = public_user_id_override
    elif auth_user_id:
        public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)

    if not public_user_id:
        raise OpenItemsSessionError("AUTH_USER_NOT_LINKED")

    cabinet_id = await _get_cabinet_id_for_user(conn, public_user_id)
    if not cabinet_id:
        raise OpenItemsSessionError("CABINET_NOT_FOUND_FOR_USER")

    is_valid_priority_item = await _priority_item_belongs_to_cabinet(
        conn,
        cabinet_id=cabinet_id,
        priority_info_request_id=priority_info_request_id,
    )
    if not is_valid_priority_item:
        raise OpenItemsSessionError("PRIORITY_INFO_REQUEST_NOT_FOUND_FOR_CABINET")

    session_row = await conn.fetchrow(
        """
        select id, cabinet_id, public_user_id, priority_info_request_id, status, created_at, updated_at
        from public.open_items_chat_sessions
        where public_user_id = $1::uuid
        and cabinet_id = $2::uuid
        and status = 'open'
        and created_at >= date_trunc('day', now())
        and created_at < date_trunc('day', now()) + interval '1 day'
        order by updated_at desc, created_at desc
        limit 1
        """,
        public_user_id,
        cabinet_id,
    )

    if session_row:
        session_row = await conn.fetchrow(
            """
            update public.open_items_chat_sessions
            set priority_info_request_id = $2::uuid
            where id = $1::uuid
            returning id, cabinet_id, public_user_id, priority_info_request_id, status, created_at, updated_at
            """,
            str(session_row["id"]),
            priority_info_request_id,
        )
    else:
        session_row = await conn.fetchrow(
            """
            insert into public.open_items_chat_sessions (
            cabinet_id,
            public_user_id,
            priority_info_request_id,
            status
            )
            values (
            $1::uuid,
            $2::uuid,
            $3::uuid,
            'open'
            )
            returning id, cabinet_id, public_user_id, priority_info_request_id, status, created_at, updated_at
            """,
            cabinet_id,
            public_user_id,
            priority_info_request_id,
        )

    session_id = str(session_row["id"])

    message_count = await conn.fetchval(
        """
        select count(*)
        from public.open_items_chat_messages
        where session_id = $1::uuid
        """,
        session_id,
    )

    return {
        "session_id": session_id,
        "cabinet_id": str(session_row["cabinet_id"]),
        "public_user_id": str(session_row["public_user_id"]),
        "priority_info_request_id": (
            str(session_row["priority_info_request_id"])
            if session_row["priority_info_request_id"]
            else None
        ),
        "status": str(session_row["status"]),
        "messages_count": int(message_count or 0),
        "is_empty": int(message_count or 0) == 0,
    }