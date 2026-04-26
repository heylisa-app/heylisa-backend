#app/api/v1/chat_open_items.py

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from asyncpg import Pool

from app.db.pool import get_pool
from app.services.auth import get_auth_user_id_from_bearer, AuthError
from app.services.open_items_chat import handle_open_items_chat_message, OpenItemsChatError

from app.services.open_items_session import (
    get_or_create_open_items_session,
    OpenItemsSessionError,
)

from app.services.open_items_intro_handler import (
    handle_open_items_intro,
    OpenItemsIntroHandlerError,
)

import os

import logging

logger = logging.getLogger("heylisa.chat.open_items")

router = APIRouter()


class OpenItemsChatRequest(BaseModel):
    session_id: str
    content: str
    priority_info_request_id: Optional[str] = None

class OpenItemsSessionRequest(BaseModel):
    priority_info_request_id: Optional[str] = None

class OpenItemsIntroRequest(BaseModel):
    session_id: str

class OpenItemsHistoryRequest(BaseModel):
    session_id: str

class OpenItemsFocusRequest(BaseModel):
    session_id: str
    priority_info_request_id: str


@router.post("/chat/open-items/message")
async def chat_open_items_message(
    body: OpenItemsChatRequest,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
    x_dev_public_user_id: str | None = Header(default=None),
):
    try:
        auth_user_id: str | None = None
        public_user_id_override: str | None = None

        env_node = (os.getenv("NODE_ENV") or "").strip().lower()
        env_environment = (os.getenv("ENVIRONMENT") or "").strip().lower()
        env_app = (os.getenv("APP_ENV") or "").strip().lower()

        is_dev = (
            env_node in {"dev", "development"}
            or env_environment in {"dev", "development"}
            or env_app in {"dev", "development"}
        )

        if authorization:
            try:
                auth_user_id = await get_auth_user_id_from_bearer(authorization)
            except AuthError as e:
                raise HTTPException(status_code=401, detail=str(e))
        elif is_dev and x_dev_public_user_id:
            public_user_id_override = x_dev_public_user_id
        else:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    try:
        async with pool.acquire() as conn:
            logger.info(
                "[OPEN_ITEMS] hit /v1/chat/open-items/message | session_id=%s | priority_info_request_id=%s",
                body.session_id,
                body.priority_info_request_id,
            )
            result = await handle_open_items_chat_message(
                conn=conn,
                session_id=body.session_id,
                content=body.content,
                priority_info_request_id=body.priority_info_request_id,
                auth_user_id=auth_user_id,
                public_user_id_override=public_user_id_override,
            )
            return result

    except OpenItemsChatError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.exception("[OPEN_ITEMS] unexpected error")
        raise HTTPException(status_code=500, detail="OPEN_ITEMS_INTERNAL_ERROR")


@router.post("/chat/open-items/session")
async def chat_open_items_session(
    body: OpenItemsSessionRequest,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
    x_dev_public_user_id: str | None = Header(default=None),
):
    auth_user_id: str | None = None
    public_user_id_override: str | None = None

    env_node = (os.getenv("NODE_ENV") or "").strip().lower()
    env_environment = (os.getenv("ENVIRONMENT") or "").strip().lower()
    env_app = (os.getenv("APP_ENV") or "").strip().lower()

    is_dev = env_node in {"dev", "development"} or env_environment in {"dev", "development"} or env_app in {"dev", "development"}

    logger.info(
        "[OPEN_ITEMS] session auth check | is_dev=%s | NODE_ENV=%s | ENVIRONMENT=%s | APP_ENV=%s | has_authorization=%s | x_dev_public_user_id=%s",
        is_dev,
        env_node,
        env_environment,
        env_app,
        bool(authorization),
        x_dev_public_user_id,
    )

    if authorization:
        try:
            auth_user_id = await get_auth_user_id_from_bearer(authorization)
        except AuthError as e:
            raise HTTPException(status_code=401, detail=str(e))
    elif is_dev and x_dev_public_user_id:
        public_user_id_override = x_dev_public_user_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        async with pool.acquire() as conn:
            result = await get_or_create_open_items_session(
                conn=conn,
                auth_user_id=auth_user_id,
                public_user_id_override=public_user_id_override,
                priority_info_request_id=body.priority_info_request_id,
            )
            return {
                "ok": True,
                **result,
            }

    except OpenItemsSessionError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("[OPEN_ITEMS] session unexpected error")
        raise HTTPException(status_code=500, detail="OPEN_ITEMS_SESSION_INTERNAL_ERROR")


@router.post("/chat/open-items/intro")
async def chat_open_items_intro(
    body: OpenItemsIntroRequest,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
    x_dev_public_user_id: str | None = Header(default=None),
):
    auth_user_id: str | None = None
    public_user_id_override: str | None = None

    env_node = (os.getenv("NODE_ENV") or "").strip().lower()
    env_environment = (os.getenv("ENVIRONMENT") or "").strip().lower()
    env_app = (os.getenv("APP_ENV") or "").strip().lower()

    is_dev = (
        env_node in {"dev", "development"}
        or env_environment in {"dev", "development"}
        or env_app in {"dev", "development"}
    )

    if authorization:
        try:
            auth_user_id = await get_auth_user_id_from_bearer(authorization)
        except AuthError as e:
            raise HTTPException(status_code=401, detail=str(e))
    elif is_dev and x_dev_public_user_id:
        public_user_id_override = x_dev_public_user_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        async with pool.acquire() as conn:
            result = await handle_open_items_intro(
                conn=conn,
                session_id=body.session_id,
                auth_user_id=auth_user_id,
                public_user_id_override=public_user_id_override,
            )
            return result

    except OpenItemsIntroHandlerError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception:
        logger.exception("[OPEN_ITEMS] intro unexpected error")
        raise HTTPException(status_code=500, detail="OPEN_ITEMS_INTRO_INTERNAL_ERROR")


@router.post("/chat/open-items/history")
async def chat_open_items_history(
    body: OpenItemsHistoryRequest,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
    x_dev_public_user_id: str | None = Header(default=None),
):
    auth_user_id: str | None = None
    public_user_id_override: str | None = None

    env_node = (os.getenv("NODE_ENV") or "").strip().lower()
    env_environment = (os.getenv("ENVIRONMENT") or "").strip().lower()
    env_app = (os.getenv("APP_ENV") or "").strip().lower()

    is_dev = (
        env_node in {"dev", "development"}
        or env_environment in {"dev", "development"}
        or env_app in {"dev", "development"}
    )

    if authorization:
        try:
            auth_user_id = await get_auth_user_id_from_bearer(authorization)
        except AuthError as e:
            raise HTTPException(status_code=401, detail=str(e))
    elif is_dev and x_dev_public_user_id:
        public_user_id_override = x_dev_public_user_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        async with pool.acquire() as conn:
            public_user_id = public_user_id_override

            if not public_user_id:
                row = await conn.fetchrow(
                    """
                    select id
                    from public.users
                    where auth_user_id = $1
                    limit 1
                    """,
                    auth_user_id,
                )
                if not row:
                    raise HTTPException(status_code=400, detail="AUTH_USER_NOT_LINKED")

                public_user_id = str(row["id"])

            session_row = await conn.fetchrow(
                """
                select id
                from public.open_items_chat_sessions
                where id = $1::uuid
                  and public_user_id = $2::uuid
                  and status = 'open'
                limit 1
                """,
                body.session_id,
                public_user_id,
            )

            if not session_row:
                raise HTTPException(status_code=400, detail="OPEN_ITEMS_SESSION_NOT_FOUND")

            rows = await conn.fetch(
                """
                select id, sender_type, role, content, metadata, sent_at
                from public.open_items_chat_messages
                where session_id = $1::uuid
                order by sent_at asc
                """,
                body.session_id,
            )

            return {
                "ok": True,
                "session_id": body.session_id,
                "messages": [
                    {
                        "id": str(r["id"]),
                        "sender_type": str(r["sender_type"]),
                        "role": str(r["role"]),
                        "content": str(r["content"] or ""),
                        "metadata": r["metadata"] or {},
                        "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
                    }
                    for r in rows
                ],
            }

    except HTTPException:
        raise

    except Exception:
        logger.exception("[OPEN_ITEMS] history unexpected error")
        raise HTTPException(status_code=500, detail="OPEN_ITEMS_HISTORY_INTERNAL_ERROR")


@router.post("/chat/open-items/focus")
async def chat_open_items_focus(
    body: OpenItemsFocusRequest,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
    x_dev_public_user_id: str | None = Header(default=None),
):
    auth_user_id: str | None = None
    public_user_id_override: str | None = None

    env_node = (os.getenv("NODE_ENV") or "").strip().lower()
    env_environment = (os.getenv("ENVIRONMENT") or "").strip().lower()
    env_app = (os.getenv("APP_ENV") or "").strip().lower()

    is_dev = (
        env_node in {"dev", "development"}
        or env_environment in {"dev", "development"}
        or env_app in {"dev", "development"}
    )

    if authorization:
        try:
            auth_user_id = await get_auth_user_id_from_bearer(authorization)
        except AuthError as e:
            raise HTTPException(status_code=401, detail=str(e))
    elif is_dev and x_dev_public_user_id:
        public_user_id_override = x_dev_public_user_id
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        async with pool.acquire() as conn:
            public_user_id = public_user_id_override

            if not public_user_id:
                row = await conn.fetchrow(
                    """
                    select id
                    from public.users
                    where auth_user_id = $1
                    limit 1
                    """,
                    auth_user_id,
                )
                if not row:
                    raise HTTPException(status_code=400, detail="AUTH_USER_NOT_LINKED")

                public_user_id = str(row["id"])

            session_row = await conn.fetchrow(
                """
                select id, cabinet_id, public_user_id, status
                from public.open_items_chat_sessions
                where id = $1::uuid
                  and public_user_id = $2::uuid
                  and status = 'open'
                limit 1
                """,
                body.session_id,
                public_user_id,
            )

            if not session_row:
                raise HTTPException(status_code=400, detail="OPEN_ITEMS_SESSION_NOT_FOUND")

            info_request_row = await conn.fetchrow(
                """
                select id, title, reason, priority, interaction_id, queue_id
                from public.cabinet_info_requests
                where id = $1::uuid
                  and cabinet_id = $2::uuid
                  and status = 'open'
                limit 1
                """,
                body.priority_info_request_id,
                str(session_row["cabinet_id"]),
            )

            if not info_request_row:
                raise HTTPException(status_code=400, detail="OPEN_ITEMS_FOCUS_ITEM_NOT_FOUND")

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
                        'event_type', 'open_items_focus_changed',
                        'source', 'backend',
                        'priority_info_request_id', $4::text,
                        'title', $5::text,
                        'reason', $6::text,
                        'priority', $7::text
                    )
                )
                returning id, content, sent_at, metadata
                """,
                body.session_id,
                "Je vois que vous regardez maintenant ce dossier. Je garde ce contexte en tête pour la suite.",
                f"focus:{body.session_id}:{body.priority_info_request_id}:{__import__('time').time()}",
                body.priority_info_request_id,
                info_request_row["title"],
                info_request_row["reason"],
                info_request_row["priority"],
            )

            return {
                "ok": True,
                "session_id": body.session_id,
                "focus_item": {
                    "id": str(info_request_row["id"]),
                    "title": info_request_row["title"],
                    "reason": info_request_row["reason"],
                    "priority": info_request_row["priority"],
                    "interaction_id": str(info_request_row["interaction_id"]) if info_request_row["interaction_id"] else None,
                    "queue_id": str(info_request_row["queue_id"]) if info_request_row["queue_id"] else None,
                },
                "assistant_message": {
                    "id": str(row["id"]),
                    "content": str(row["content"] or ""),
                    "sent_at": row["sent_at"].isoformat() if row["sent_at"] else None,
                    "metadata": row["metadata"] or {},
                },
            }

    except HTTPException:
        raise

    except Exception:
        logger.exception("[OPEN_ITEMS] focus unexpected error")
        raise HTTPException(status_code=500, detail="OPEN_ITEMS_FOCUS_INTERNAL_ERROR")