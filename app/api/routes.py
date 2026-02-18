#app/api/routes.py

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from asyncpg import Pool

from app.db.pool import get_pool
from app.services.quota import get_quota_status
from app.services.auth import get_auth_user_id_from_bearer, AuthError
from app.services.chat import handle_chat_message, ChatError
from app.services.chat_intro import handle_chat_intro, ChatIntroError
import logging
import traceback

logger = logging.getLogger("heylisa.chat")

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
    
    # Auth (DEV permissif)
    try:
        auth_user_id = await get_auth_user_id_from_bearer(authorization)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))

    async with pool.acquire() as conn:
        # 1) Conversation -> public_user_id
        row = await conn.fetchrow(
            "select user_id from public.conversations where id = $1::uuid",
            body.conversation_id,
        )
        if not row:
            raise HTTPException(status_code=404, detail="CONVERSATION_NOT_FOUND")

        public_user_id = str(row["user_id"])

        # 2) Ownership check (best effort, comme handle_chat_message)
        if auth_user_id:
            expected_public_user_id = await conn.fetchval(
                "select id from public.users where auth_user_id = $1",
                auth_user_id,
            )
            if not expected_public_user_id:
                raise HTTPException(status_code=401, detail="No public user linked to this auth user")
            if str(expected_public_user_id) != str(public_user_id):
                raise HTTPException(status_code=403, detail="Conversation does not belong to authenticated user")

        try:
            out = await handle_chat_intro(
                conn,
                conversation_id=body.conversation_id,
                public_user_id=public_user_id,
            )
            return out
        except ChatIntroError as e:
            # erreurs fonctionnelles => le front peut aussi fallback
            return {"ok": False, "code": "INTRO_BAD_REQUEST", "message": str(e)[:220]}
        except Exception as e:
            # ✅ soft-fail même sur crash inattendu
            return {"ok": False, "code": "INTRO_INTERNAL", "message": str(e)[:220]}



@router.post("/v1/chat/message")
async def chat_message(
    body: ChatMessageIn,
    pool: Pool = Depends(get_pool),
    authorization: str | None = Header(default=None),
):
    logger.info("[CHAT] /v1/chat/message hit | has_auth=%s | auth_prefix=%s",
                bool(authorization),
                (authorization or "")[:20])
    # Auth (DEV permissif)
    try:
        auth_user_id = await get_auth_user_id_from_bearer(authorization)
    except AuthError as e:
        logger.warning("[CHAT] auth failed: %s", str(e))
        raise HTTPException(status_code=401, detail=str(e))

    async with pool.acquire() as conn:
        try:
            out = await handle_chat_message(
                conn,
                conversation_id=body.conversation_id,
                user_message_id=body.user_message_id,
                auth_user_id=auth_user_id,
            )
            return out
        except ChatError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.exception(
                "[CHAT] chat_message crashed",
                extra={
                    "conversation_id": body.conversation_id,
                    "user_message_id": body.user_message_id,
                    "auth_user_id": auth_user_id,
                },
            )
            print("[CHAT] traceback:\n", traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)[:120]}")