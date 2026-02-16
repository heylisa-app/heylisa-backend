# app/api/v1/chat_intro.py
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from asyncpg import Connection

from app.core.db import get_db_conn  # adapte si ton dépendency s'appelle autrement
from app.services.chat_intro import handle_chat_intro

router = APIRouter(prefix="/v1/chat", tags=["chat"])


class ChatIntroRequest(BaseModel):
    conversation_id: str


@router.post("/intro")
async def chat_intro(payload: ChatIntroRequest, conn: Connection = Depends(get_db_conn)):
    # ⚠️ ici on prend public_user_id via la conversation
    row = await conn.fetchrow(
        "select user_id from public.conversations where id = $1::uuid",
        payload.conversation_id,
    )
    if not row:
        return {"ok": False, "error": "CONVERSATION_NOT_FOUND"}

    public_user_id = str(row["user_id"])
    return await handle_chat_intro(
        conn,
        conversation_id=str(payload.conversation_id),
        public_user_id=public_user_id,
    )