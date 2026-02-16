import json
from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.agents.orchestrator import OrchestratorAgent
from app.services.plan_executor import PlanExecutor
from app.services.context_loader import load_context_light

from app.core.chat_logger import chat_logger
from app.integrations.n8n_userfacts import fire_userfact_webhook
from app.services.message_flags import extract_and_clean_message_flags


class ChatError(Exception):
    pass


async def _get_public_user_id_from_auth(conn: Connection, auth_user_id: str) -> str | None:
    row = await conn.fetchrow(
        "select id from public.users where auth_user_id = $1",
        auth_user_id,
    )
    return row["id"] if row else None


async def _get_user_message(conn: Connection, conversation_id: str, user_message_id: str):
    return await conn.fetchrow(
        """
        select id, conversation_id, user_id, content, metadata
        from public.conversation_messages
        where id = $1 and conversation_id = $2
        """,
        user_message_id,
        conversation_id,
    )


async def _get_assistant_message(conn: Connection, assistant_message_id: str):
    return await conn.fetchrow(
        """
        select id, content, sent_at
        from public.conversation_messages
        where id = $1
        """,
        assistant_message_id,
    )


async def handle_chat_message(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
) -> dict:
    # 1) Load user message
    msg = await _get_user_message(conn, conversation_id, user_message_id)
    if not msg:
        raise ChatError("User message not found for this conversation")

    chat_logger.info(
        "chat.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        auth_user_id=str(auth_user_id) if auth_user_id else None,
        public_user_id=str(msg["user_id"]) if msg.get("user_id") else None,
        user_content=(msg["content"] or "")[:200],
    )

    public_user_id = msg["user_id"]

    # 2) Ownership check (best effort)
    # If auth_user_id exists => ensure msg.user_id belongs to auth_user_id
    if auth_user_id:
        expected_public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)
        if not expected_public_user_id:
            raise ChatError("No public user linked to this auth user")
        if str(expected_public_user_id) != str(public_user_id):
            raise ChatError("Message does not belong to authenticated user")

    # 3) Idempotence: if already processed, return existing assistant msg
    meta = msg["metadata"] or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}

    existing_assistant_id = meta.get("assistant_message_id")
    if existing_assistant_id:
        existing = await _get_assistant_message(conn, existing_assistant_id)
        if existing:
            chat_logger.info(
                "chat.cache_hit",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                assistant_message_id=str(existing_assistant_id),
            )
            return {
                "ok": True,
                "assistant_message": {
                    "id": str(existing["id"]),
                    "sent_at": existing["sent_at"].isoformat(),
                    "content": existing["content"],
                },
                "provider": {"primary": "cache", "fallback_used": False},
            }

    # 4) Orchestrator -> plan
    llm = LLMRuntime()
    orchestrator = OrchestratorAgent(llm)

    chat_logger.info(
        "chat.orchestrator.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )

    # 4bis) Load context (light) for orchestrator
    ctx = await load_context_light(
        conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    chat_logger.info(
        "chat.ctx.loaded",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        has_user=bool((ctx or {}).get("user")),
        locale=((ctx or {}).get("settings") or {}).get("locale_main"),
        timezone=((ctx or {}).get("settings") or {}).get("timezone"),
        free_quota_used=((ctx or {}).get("settings") or {}).get("free_quota_used"),
        free_quota_limit=((ctx or {}).get("settings") or {}).get("free_quota_limit"),
        intro_smalltalk_turns=((ctx or {}).get("settings") or {}).get("intro_smalltalk_turns"),
        intro_smalltalk_done=((ctx or {}).get("settings") or {}).get("intro_smalltalk_done"),
        last_messages_count=len((ctx or {}).get("messages") or []),
    )

    orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

    plan_nodes = []
    try:
        for n in (orch.plan or {}).get("nodes", []):
            if isinstance(n, dict):
                plan_nodes.append({"id": n.get("id"), "type": n.get("type")})
    except Exception:
        plan_nodes = []

    chat_logger.info(
        "chat.orchestrator.result",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        orch_ok=bool(getattr(orch, "ok", False)),
        intent=str(getattr(orch, "intent", "")),
        language=str(getattr(orch, "language", "")),
        need_web=bool(getattr(orch, "need_web", False)),
        confidence=float(getattr(orch, "confidence", 0.0) or 0.0),
        plan_nodes=plan_nodes[:8],
    )

    # 5) Execute plan (tools + response_writer)
    executor = PlanExecutor(
        conn=conn,
        llm=llm,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
        user_message=str(msg["content"]),
    )

    chat_logger.info(
        "chat.executor.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )
    try:
        exec_out = await executor.run(plan=orch.plan)
        reply_text_raw = exec_out["answer"]

        # ✅ Nettoyage des flags de fin de message (aha_moment / onboarding_abort)
        reply_text, flags = extract_and_clean_message_flags(reply_text_raw)

        provider = {
            "primary": "orchestrated",
            "fallback_used": (orch.ok is False),
            "orchestrator": {"provider": (orch.debug or {}).get("meta", {}).get("provider")},
        }

        # ✅ Ajoute les flags au provider/meta (pour debug et analytics)
        provider["flags"] = flags.to_metadata()
        chat_logger.info(
            "chat.executor.done",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            answer_len=len(reply_text or ""),
            provider_primary=provider.get("primary"),
            fallback_used=bool(provider.get("fallback_used")),
        )
        # tu peux aussi stocker exec_out["debug"] en metadata si tu veux
    except Exception as e:
        # filet de sécurité ultime
        reply_text = "Désolé — j’ai eu un souci technique. Réessaie dans quelques secondes."
        provider = {"primary": "error_fallback", "fallback_used": True, "error": str(e)[:160], "flags": {"aha_moment": False, "onboarding_abort": False}}

        chat_logger.error(
            "chat.executor.error",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            error=str(e)[:300],
            exc_info=True,
        )


    # 6) Insert assistant message (idempotent via dedupe_key)
    dedupe_key = f"a:{conversation_id}:{user_message_id}"

    # --- Persist orchestration decision into assistant metadata (for continuity) ---
    mode = None
    try:
        for n in (orch.plan or {}).get("nodes", []):
            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                mode = ((n.get("inputs") or {}) if isinstance(n.get("inputs"), dict) else {}).get("mode")
                break
    except Exception:
        mode = None

    # --- intent_final robuste (source: orch.debug.intent_final si dispo) ---
    intent_final = None
    try:
        dbg = getattr(orch, "debug", None)
        if isinstance(dbg, dict):
            intent_final = dbg.get("intent_final") or dbg.get("intent")  # fallback
    except Exception:
        intent_final = None

    if not intent_final:
        intent_final = getattr(orch, "intent", None)

    assistant_meta = {
        "event_type": "backend_chat",
        "provider": provider,

        # continuity keys
        "orch": {
            "intent_final": str(intent_final or ""),
            "mode": str(mode or ""),
            "need_web": bool(getattr(orch, "need_web", False)),
            "confidence": float(getattr(orch, "confidence", 0.0) or 0.0),
        }
    }

    inserted = await conn.fetchrow(
        """
        insert into public.conversation_messages
        (conversation_id, user_id, sender_type, role, content, metadata, dedupe_key)
        values
        ($1, $2::uuid, 'lisa', 'assistant', $3, $4::jsonb, $5)
        on conflict (dedupe_key) do update
        set content = excluded.content,
            metadata = excluded.metadata
        returning id, sent_at
        """,
        conversation_id,
        public_user_id,
        reply_text,
        json.dumps(assistant_meta, default=str),
        dedupe_key,
    )

    assistant_message_id = str(inserted["id"])

    # ✅ Post-actions (AHA moment / abort) — best effort, ne casse pas le chat
    try:
        if provider.get("flags", {}).get("aha_moment") is True:
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'complete',
                    discovery_completed_at = now()
                where user_id = $1
                """,
                public_user_id,
            )
        elif provider.get("flags", {}).get("onboarding_abort") is True:
            await conn.execute(
                """
                update public.user_settings
                set discovery_status = 'aborted'
                where user_id = $1
                and coalesce(discovery_status,'pending') <> 'complete'
                """,
                public_user_id,
            )
    except Exception as _e:
        chat_logger.info("chat.flags.persist_error", error=str(_e)[:180])

    chat_logger.info(
        "chat.persisted",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        assistant_message_id=str(assistant_message_id),
    )

    # 6bis) Fire-and-forget user facts catcher (must not impact chat latency)
    chat_logger.info("userfacts.hook.before", conversation_id=str(conversation_id), user_message_id=str(user_message_id))

    try:
        payload = {
            "public_user_id": str(public_user_id),
            "conversation_id": str(conversation_id),
            "user_message_id": str(user_message_id),
            "assistant_message_id": str(assistant_message_id),
            "user_text": (msg["content"] or ""),
            "locale": ((ctx or {}).get("settings") or {}).get("locale_main"),
            "timezone": ((ctx or {}).get("settings") or {}).get("timezone"),
        }

        chat_logger.info("userfacts.hook.payload_ready", public_user_id=str(public_user_id))

        # ✅ IMPORTANT : si fire_userfact_webhook est async -> create_task
        import asyncio
        asyncio.create_task(fire_userfact_webhook(payload))

        chat_logger.info("userfacts.hook.task_scheduled")

    except Exception as e:
        chat_logger.info("userfacts.webhook.call_error", error=str(e)[:180])

    # 7) Update user msg metadata with assistant id (idempotence marker)
    # We merge existing metadata (best effort)
    await conn.execute(
        """
        update public.conversation_messages
        set metadata = coalesce(metadata, '{}'::jsonb) ||
        jsonb_build_object(
            'processed_by_backend', true,
            'assistant_message_id', $2::uuid
        )
        where id = $1::uuid
        """,
        user_message_id,
        assistant_message_id,
    )

    chat_logger.info(
        "chat.end",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        assistant_message_id=str(assistant_message_id),
    )

    return {
        "ok": True,
        "assistant_message": {
            "id": assistant_message_id,
            "sent_at": inserted["sent_at"].isoformat(),
            "content": reply_text,
        },
        "provider": provider,
    }