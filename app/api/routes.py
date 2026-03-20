#app/api/routes.py

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from asyncpg import Pool

from app.db.pool import get_pool
from app.services.quota import get_quota_status
from app.services.auth import get_auth_user_id_from_bearer, AuthError
from app.services.chat import handle_chat_message, handle_chat_message_stream, ChatError
from app.services.chat_intro import handle_chat_intro, handle_chat_intro_stream, ChatIntroError
from datetime import datetime
from app.settings import settings

import logging
import traceback

logger = logging.getLogger("heylisa.chat")

router = APIRouter()

def _sse_event(event_name: str, data: dict) -> str:
    import json
    return f"event: {event_name}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _sse_response_headers() -> dict:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }


@router.get("/health")
async def health():
    return {
        "ok": True,
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
    }

@router.get("/ready")
async def ready(pool: Pool = Depends(get_pool)):
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


class ChatMessageIn(BaseModel):
    conversation_id: str
    user_message_id: str


class ChatIntroIn(BaseModel):
    conversation_id: str

@router.post("/v1/chat/intro")
async def chat_intro(
    body: ChatIntroIn,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
):
    print("🔥 HIT /v1/chat/intro", body, authorization)

    try:
        auth_user_id = await get_auth_user_id_from_bearer(authorization)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    async def event_generator():
        yield _sse_event("ack", {
            "ok": True,
            "conversation_id": body.conversation_id,
            "request_type": "chat_intro",
        })

        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "select user_id from public.conversations where id = $1::uuid",
                body.conversation_id,
            )
            if not row:
                yield _sse_event("error", {
                    "ok": False,
                    "code": "CONVERSATION_NOT_FOUND",
                    "message": "Conversation not found",
                    "retryable": False,
                })
                return

            public_user_id = str(row["user_id"])

            if auth_user_id:
                expected_public_user_id = await conn.fetchval(
                    "select id from public.users where auth_user_id = $1",
                    auth_user_id,
                )
                if not expected_public_user_id:
                    yield _sse_event("error", {
                        "ok": False,
                        "code": "FORBIDDEN",
                        "message": "No public user linked to this auth user",
                        "retryable": False,
                    })
                    return

                if str(expected_public_user_id) != str(public_user_id):
                    yield _sse_event("error", {
                        "ok": False,
                        "code": "FORBIDDEN",
                        "message": "Conversation does not belong to authenticated user",
                        "retryable": False,
                    })
                    return

            try:
                meta_sent = False

                async for ev in handle_chat_intro_stream(
                    conn,
                    conversation_id=body.conversation_id,
                    public_user_id=public_user_id,
                ):
                    etype = ev.get("type")

                    if etype == "delta":
                        if not meta_sent:
                            yield _sse_event("meta", {
                                "mode": "intro_onboarding",
                                "message_id": None,
                                "stream_id": f"intro:{body.conversation_id}",
                                "can_retry": False,
                            })
                            meta_sent = True

                        yield _sse_event("delta", {
                            "text": str(ev.get("text") or ""),
                        })
                        continue

                    if etype == "done":
                        assistant_message = ev.get("assistant_message") or {}
                        provider = ev.get("provider") or {}

                        if not meta_sent:
                            yield _sse_event("meta", {
                                "mode": "intro_onboarding",
                                "message_id": assistant_message.get("id"),
                                "stream_id": f"intro:{body.conversation_id}",
                                "can_retry": False,
                            })

                        yield _sse_event("done", {
                            "ok": True,
                            "assistant_message": assistant_message,
                            "provider": provider,
                        })
                        return

            except ChatIntroError as e:
                yield _sse_event("error", {
                    "ok": False,
                    "code": "INTRO_BAD_REQUEST",
                    "message": str(e)[:220],
                    "retryable": False,
                })
                return

            except Exception as e:
                yield _sse_event("error", {
                    "ok": False,
                    "code": "INTRO_INTERNAL",
                    "message": str(e)[:220],
                    "retryable": True,
                })
                return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_sse_response_headers(),
    )



@router.post("/v1/chat/message")
async def chat_message(
    body: ChatMessageIn,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
):
    logger.info(
        "[CHAT] /v1/chat/message hit | has_auth=%s | auth_prefix=%s",
        bool(authorization),
        (authorization or "")[:20],
    )

    try:
        auth_user_id = await get_auth_user_id_from_bearer(authorization)
    except AuthError as e:
        logger.warning("[CHAT] auth failed: %s", str(e))
        raise HTTPException(status_code=401, detail=str(e))

    async def event_generator():
        yield _sse_event("ack", {
            "ok": True,
            "conversation_id": body.conversation_id,
            "request_type": "chat_message",
        })

        async with pool.acquire() as conn:
            try:
                meta_sent = False

                async for ev in handle_chat_message_stream(
                    conn,
                    conversation_id=body.conversation_id,
                    user_message_id=body.user_message_id,
                    auth_user_id=auth_user_id,
                ):
                    etype = ev.get("type")

                    if etype == "delta":
                        if not meta_sent:
                            yield _sse_event("meta", {
                                "mode": "streaming",
                                "message_id": None,
                                "stream_id": f"stream:{body.user_message_id}",
                                "can_retry": True,
                            })
                            meta_sent = True

                        yield _sse_event("delta", {
                            "text": str(ev.get("text") or ""),
                        })
                        continue

                    if etype == "error":
                        yield _sse_event("error", {
                            "ok": False,
                            "code": str(ev.get("error") or "CHAT_INTERNAL"),
                            "message": str(ev.get("message") or "Lisa n’a pas pu répondre pour le moment."),
                            "retryable": True,
                            "debug": ev.get("debug") or {},
                        })
                        return

                    if etype == "done":
                        assistant_message = ev.get("assistant_message") or {}
                        provider = ev.get("provider") or {}

                        if not meta_sent:
                            yield _sse_event("meta", {
                                "mode": "streaming",
                                "message_id": assistant_message.get("id"),
                                "stream_id": f"stream:{body.user_message_id}",
                                "can_retry": True,
                            })

                        yield _sse_event("done", {
                            "ok": True,
                            "assistant_message": assistant_message,
                            "provider": provider,
                        })
                        return

            except ChatError as e:
                yield _sse_event("error", {
                    "ok": False,
                    "code": "CHAT_BAD_REQUEST",
                    "message": str(e),
                    "retryable": False,
                })
                return

            except Exception as e:
                logger.exception(
                    "[CHAT] chat_message_stream crashed",
                    extra={
                        "conversation_id": body.conversation_id,
                        "user_message_id": body.user_message_id,
                        "auth_user_id": auth_user_id,
                    },
                )
                print("[CHAT] traceback:\n", traceback.format_exc())
                yield _sse_event("error", {
                    "ok": False,
                    "code": "CHAT_INTERNAL",
                    "message": f"Internal error: {str(e)[:120]}",
                    "retryable": True,
                })
                return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=_sse_response_headers(),
    )