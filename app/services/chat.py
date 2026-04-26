# app/services/chat.py

import json
from typing import AsyncIterator

from asyncpg import Connection

from app.agents.orchestrator import OrchestratorAgent
from app.core.chat_logger import chat_logger
from app.integrations.n8n_custom_request import fire_custom_request_webhook
from app.integrations.n8n_task_execution import fire_task_execution_webhook
from app.integrations.n8n_userfacts import fire_userfact_webhook
from app.llm.runtime import LLMRuntime
from app.services.context_loader_v2 import load_context_light
from app.services.message_flags import extract_and_clean_message_flags
from app.services.plan_executor import PlanExecutor
from app.services.seek_infos_followup import handle_seek_infos_followup

SAFE_FALLBACK_ANSWER = "Désolé — je n’ai pas réussi à générer une réponse. Faudrait réessayer."



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



async def _get_last_seek_infos_anchor_message(conn: Connection, conversation_id: str):
    rows = await conn.fetch(
        """
        select id, content, sent_at, metadata
        from public.conversation_messages
        where conversation_id = $1::uuid
          and sender_type = 'lisa'
          and role = 'assistant'
        order by sent_at desc, id desc
        limit 20
        """,
        conversation_id,
    )

    for row in rows:
        msg = dict(row)
        if _extract_seek_infos_context_from_last_lisa(msg):
            return msg

    return None


def _safe_meta_dict(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _extract_seek_infos_context_from_last_lisa(last_lisa_msg) -> dict | None:
    if not last_lisa_msg:
        return None

    meta = _safe_meta_dict(last_lisa_msg.get("metadata"))
    if not meta:
        return None

    event_type = str(meta.get("event_type") or "").strip().lower()
    proactive_kind = str(meta.get("proactive_kind") or "").strip().lower()
    awaiting_internal_reply = bool(meta.get("awaiting_internal_reply") is True)

    if event_type != "lisa_proactive_message":
        return None

    if proactive_kind != "seek_infos":
        return None

    if not awaiting_internal_reply:
        return None

    return {
        "event_type": event_type,
        "proactive_kind": proactive_kind,
        "awaiting_internal_reply": awaiting_internal_reply,
        "queue_id": str(meta.get("queue_id") or "").strip() or None,
        "seek_request_id": str(meta.get("seek_request_id") or "").strip() or None,
        "interaction_id": str(meta.get("interaction_id") or "").strip() or None,
        "schema_version": str(meta.get("schema_version") or "").strip() or None,
        "created_at": str(meta.get("created_at") or "").strip() or None,
        "assistant_message_id": str(last_lisa_msg.get("id") or "").strip() or None,
        "assistant_sent_at": (
            last_lisa_msg["sent_at"].isoformat()
            if last_lisa_msg.get("sent_at")
            else None
        ),
        "assistant_content": str(last_lisa_msg.get("content") or ""),
    }



def _extract_task_execution_context_from_orch(orch) -> dict:
    try:
        plan = getattr(orch, "plan", None)
        if not isinstance(plan, dict):
            return {}

        for node in plan.get("nodes", []):
            if isinstance(node, dict) and node.get("type") == "agent.response_writer":
                inputs = node.get("inputs") or {}
                if isinstance(inputs, dict):
                    tec = inputs.get("task_execution_context")
                    if isinstance(tec, dict):
                        return tec

        return {}

    except Exception:
        return {}

def _hydrate_orch_brain_fields(orch) -> None:
    debug = getattr(orch, "debug", {}) or {}

    orch.primary_brain_key = debug.get("primary_brain_key")
    orch.secondary_brain_key = debug.get("secondary_brain_key")
    orch.secondary_brain_reason = debug.get("secondary_brain_reason")
    orch.resume_loop_id = debug.get("resume_loop_id")
    orch.keep_warm_topic = bool(debug.get("keep_warm_topic") is True)


def _extract_response_writer_inputs_from_orch(orch) -> dict:
    try:
        plan = getattr(orch, "plan", None)
        if not isinstance(plan, dict):
            return {}

        for node in plan.get("nodes", []):
            if isinstance(node, dict) and node.get("type") == "agent.response_writer":
                inputs = node.get("inputs") or {}
                return inputs if isinstance(inputs, dict) else {}

        return {}
    except Exception:
        return {}

async def _insert_or_update_assistant_message(
    conn: Connection,
    *,
    conversation_id: str,
    public_user_id: str,
    user_message_id: str,
    reply_text: str,
    provider: dict,
    orch,
) -> dict:
    dedupe_key = f"a:{conversation_id}:{user_message_id}"

    rw_inputs = _extract_response_writer_inputs_from_orch(orch)
    mode = rw_inputs.get("mode")

    intent_final = None
    try:
        dbg = getattr(orch, "debug", None)
        if isinstance(dbg, dict):
            intent_final = dbg.get("intent_final") or dbg.get("intent")
    except Exception:
        intent_final = None

    if not intent_final:
        intent_final = getattr(orch, "intent", None)

    # -----------------------------
    # Resolve brain metadata
    # -----------------------------
    runtime_state = rw_inputs.get("runtime_state") or rw_inputs.get("state")
    primary_brain_key = rw_inputs.get("primary_brain_key")
    secondary_brain_key = rw_inputs.get("secondary_brain_key")
    secondary_brain_reason = rw_inputs.get("secondary_brain_reason")
    resume_loop_id = rw_inputs.get("resume_loop_id")
    keep_warm_topic = bool(rw_inputs.get("keep_warm_topic") is True)

    def resolve_brain_key(
        intent: str | None,
        runtime_state: str | None,
        primary_brain_key: str | None,
    ) -> str:
        if primary_brain_key:
            return str(primary_brain_key)

        if runtime_state == "seek_infos_active":
            return "seek_infos_followup"

        if intent:
            return str(intent)

        return "default"

    brain_key = resolve_brain_key(intent_final, runtime_state, primary_brain_key)

    assistant_meta = {
        "event_type": "backend_chat",
        "provider": provider,
        "brain": {
            "brain_key": brain_key,
            "primary_brain_key": str(primary_brain_key or ""),
            "secondary_brain_key": str(secondary_brain_key or ""),
            "secondary_brain_reason": str(secondary_brain_reason or ""),
            "resume_loop_id": str(resume_loop_id or ""),
            "keep_warm_topic": bool(keep_warm_topic),
            "intent": str(intent_final or ""),
            "runtime_state": str(runtime_state or ""),
        },
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

    return {
        "assistant_message_id": assistant_message_id,
        "sent_at": inserted["sent_at"].isoformat(),
        "assistant_meta": assistant_meta,
    }

async def _insert_seek_infos_assistant_message(
    conn: Connection,
    *,
    conversation_id: str,
    public_user_id: str,
    user_message_id: str,
    reply_text: str,
    assistant_meta: dict,
) -> dict:
    dedupe_key = f"lisa:{conversation_id}:seek_infos_followup:{user_message_id}"

    inserted = await conn.fetchrow(
        """
        insert into public.conversation_messages
        (
            conversation_id,
            user_id,
            sender_type,
            role,
            content,
            sent_at,
            metadata,
            dedupe_key
        )
        values
        (
            $1::uuid,
            $2::uuid,
            'lisa',
            'assistant',
            $3::text,
            now(),
            $4::jsonb,
            $5::text
        )
        on conflict (dedupe_key) do update
        set content = excluded.content,
            metadata = excluded.metadata
        returning id, sent_at, content
        """,
        conversation_id,
        public_user_id,
        reply_text,
        json.dumps(assistant_meta, default=str),
        dedupe_key,
    )

    assistant_message_id = str(inserted["id"])

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

    return {
        "assistant_message_id": assistant_message_id,
        "sent_at": inserted["sent_at"].isoformat(),
        "content": inserted["content"],
    }


async def _postprocess_assistant_message(
    conn: Connection,
    *,
    public_user_id: str,
    ctx: dict,
    provider: dict,
    msg,
    reply_text: str,
    orch,
    conversation_id: str,
    user_message_id: str,
    assistant_message_id: str,
) -> None:
    """
    Post-process minimal V1 :
    - déclenche uniquement le webhook userfacts
    - ne remet PAS les writes legacy onboarding / smalltalk / discovery
    """
    chat_logger.info(
        "userfacts.hook.before",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )

    try:
        payload = {
            "source": "chat_message",
            "public_user_id": str(public_user_id),
            "conversation_id": str(conversation_id),
            "conversation_channel": ((ctx or {}).get("conversation") or {}).get("channel"),
            "user_message_id": str(user_message_id),
            "assistant_message_id": str(assistant_message_id),
            "user_text": (msg["content"] or ""),
            "assistant_text": "",  # volontairement vide ici pour rester minimal
            "locale": ((ctx or {}).get("settings") or {}).get("locale_main"),
            "timezone": ((ctx or {}).get("settings") or {}).get("timezone"),
            "cabinet_account_id": ((ctx or {}).get("cabinet") or {}).get("id"),
            "member_role": ((ctx or {}).get("member") or {}).get("role"),
            "member_job_role": ((ctx or {}).get("member") or {}).get("job_role"),
        }

        chat_logger.info(
            "userfacts.hook.payload_ready",
            public_user_id=str(public_user_id),
        )

        import asyncio
        asyncio.create_task(fire_userfact_webhook(payload))

        chat_logger.info("userfacts.hook.task_scheduled")

    except Exception as e:
        chat_logger.info("userfacts.webhook.call_error", error=str(e)[:180])


    try:
        provider_flags = ((provider or {}).get("flags") or {})
        raw_task_execution_flag = bool(provider_flags.get("task_to_execute") is True)
        raw_custom_request_flag = bool(provider_flags.get("custom_request") is True)

        task_execution_context = _extract_task_execution_context_from_orch(orch)

        task_detected = bool((task_execution_context or {}).get("task_detected") is True)
        task_key = str((task_execution_context or {}).get("task_key") or "").strip()
        task_status = str((task_execution_context or {}).get("task_status") or "").strip().lower()
        can_execute_now = bool((task_execution_context or {}).get("can_execute_now") is True)

        # -----------------------------------
        # Verrous déterministes backend
        # -----------------------------------
        effective_task_execution = bool(
            raw_task_execution_flag
            and task_detected
            and bool(task_key)
            and task_status == "active"
            and can_execute_now
        )

        effective_custom_request = bool(
            raw_custom_request_flag
            and not effective_task_execution
            and (
                (not task_detected)
                or task_status in {"unknown", "disabled", ""}
            )
        )

        chat_logger.info(
            "task_hooks.flags.resolved",
            raw_task_execution_flag=raw_task_execution_flag,
            raw_custom_request_flag=raw_custom_request_flag,
            effective_task_execution=effective_task_execution,
            effective_custom_request=effective_custom_request,
            task_key=task_key or None,
            task_status=task_status or None,
            task_detected=task_detected,
            can_execute_now=can_execute_now,
            task_execution_context=task_execution_context,
        )

        if effective_task_execution:
            payload = {
                "source": "chat_task_execution",
                "public_user_id": str(public_user_id),
                "conversation_id": str(conversation_id),
                "conversation_channel": ((ctx or {}).get("conversation") or {}).get("channel"),
                "user_message_id": str(user_message_id),
                "assistant_message_id": str(assistant_message_id),
                "user_text": (msg["content"] or ""),
                "assistant_text": reply_text,
                "cabinet_account_id": ((ctx or {}).get("cabinet") or {}).get("id"),
                "member_role": ((ctx or {}).get("member") or {}).get("role"),
                "member_job_role": ((ctx or {}).get("member") or {}).get("job_role"),
                "task_execution_context": task_execution_context,
            }

            chat_logger.info(
                "task_execution.hook.payload_ready",
                public_user_id=str(public_user_id),
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                assistant_message_id=str(assistant_message_id),
                task_key=task_key or None,
                task_status=task_status or None,
            )

            import asyncio
            asyncio.create_task(fire_task_execution_webhook(payload))

            chat_logger.info("task_execution.hook.task_scheduled")

        if effective_custom_request:
            payload = {
                "source": "chat_custom_request",
                "public_user_id": str(public_user_id),
                "conversation_id": str(conversation_id),
                "conversation_channel": ((ctx or {}).get("conversation") or {}).get("channel"),
                "user_message_id": str(user_message_id),
                "assistant_message_id": str(assistant_message_id),
                "user_text": (msg["content"] or ""),
                "assistant_text": reply_text,
                "cabinet_account_id": ((ctx or {}).get("cabinet") or {}).get("id"),
                "member_role": ((ctx or {}).get("member") or {}).get("role"),
                "member_job_role": ((ctx or {}).get("member") or {}).get("job_role"),
                "task_execution_context": task_execution_context,
            }

            chat_logger.info(
                "custom_request.hook.payload_ready",
                public_user_id=str(public_user_id),
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                assistant_message_id=str(assistant_message_id),
                task_key=task_key or None,
                task_status=task_status or None,
            )

            import asyncio
            asyncio.create_task(fire_custom_request_webhook(payload))

            chat_logger.info("custom_request.hook.task_scheduled")

    except Exception as e:
        chat_logger.info("task_hooks.webhook.call_error", error=str(e)[:180])


async def _rerun_after_escalation(
    *,
    reason: str,
    ctx: dict,
    orchestrator,
    msg,
    conn: Connection,
    llm,
    public_user_id: str,
    conversation_id: str,
):
    ctx = ctx or {}
    ctx.setdefault("gates", {})

    if reason == "need_web":
        ctx["gates"]["force_need_web"] = True
    elif reason == "need_docs":
        ctx["gates"]["force_need_docs"] = True

    orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)
    _hydrate_orch_brain_fields(orch)

    executor = PlanExecutor(
        conn=conn,
        llm=llm,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
        user_message=str(msg["content"]),
    )

    final_answer = None
    exec_final_debug = {}
    exec_provider_primary = (
        (getattr(orch, "debug", {}) or {})
        .get("meta", {})
        .get("provider")
        or "orchestrated"
    )

    async for ev in executor.run_stream(plan=orch.plan):
        etype = ev.get("type")

        if etype == "delta":
            yield {
                "type": "delta",
                "text": str(ev.get("text") or ""),
            }

        elif etype == "error":
            yield {
                "type": "result",
                "orch": orch,
                "final_answer": final_answer,
                "exec_final_debug": exec_final_debug,
                "exec_provider_primary": exec_provider_primary,
                "error_event": ev,
            }
            return

        elif etype == "final":
            final_answer = ev.get("answer") or SAFE_FALLBACK_ANSWER
            exec_final_debug = ev.get("debug") or {}
            exec_provider_primary = (
                (getattr(orch, "debug", {}) or {})
                .get("meta", {})
                .get("provider")
                or "orchestrated"
            )

    yield {
        "type": "result",
        "orch": orch,
        "final_answer": final_answer,
        "exec_final_debug": exec_final_debug,
        "exec_provider_primary": exec_provider_primary,
        "error_event": None,
    }

async def _prepare_chat_request(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
):
    msg = await _get_user_message(conn, conversation_id, user_message_id)
    if not msg:
        raise ChatError("User message not found for this conversation")

    public_user_id = msg["user_id"]

    if auth_user_id:
        expected_public_user_id = await _get_public_user_id_from_auth(conn, auth_user_id)
        if not expected_public_user_id:
            raise ChatError("No public user linked to this auth user")
        if str(expected_public_user_id) != str(public_user_id):
            raise ChatError("Message does not belong to authenticated user")

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
            return {
                "msg": msg,
                "public_user_id": public_user_id,
                "cached_assistant": {
                    "id": str(existing["id"]),
                    "sent_at": existing["sent_at"].isoformat(),
                    "content": existing["content"],
                },
            }

    return {
        "msg": msg,
        "public_user_id": public_user_id,
        "cached_assistant": None,
    }



async def handle_chat_message_stream(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
) -> AsyncIterator[dict]:
    prep = await _prepare_chat_request(
        conn,
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        auth_user_id=auth_user_id,
    )

    msg = prep["msg"]
    public_user_id = prep["public_user_id"]

    if prep["cached_assistant"]:
        yield {
            "type": "done",
            "assistant_message": prep["cached_assistant"],
            "provider": {"primary": "cache", "fallback_used": False},
        }
        return

    # -------------------------------------------------
    # SEEK_INFOS FOLLOWUP DETECTION
    # -------------------------------------------------
    last_lisa_msg = await _get_last_seek_infos_anchor_message(conn, conversation_id)
    seek_infos_ctx = _extract_seek_infos_context_from_last_lisa(last_lisa_msg)

    if seek_infos_ctx:
        chat_logger.info(
            "chat.seek_infos_followup.detected",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            public_user_id=str(public_user_id),
            queue_id=seek_infos_ctx.get("queue_id"),
            seek_request_id=seek_infos_ctx.get("seek_request_id"),
            interaction_id=seek_infos_ctx.get("interaction_id"),
            assistant_message_id=seek_infos_ctx.get("assistant_message_id"),
        )

        result = await handle_seek_infos_followup(
            conn,
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            public_user_id=str(public_user_id),
            seek_infos_context=seek_infos_ctx,
        )

        assistant_text = str((result or {}).get("assistant_text") or "").strip()
        if not assistant_text:
            assistant_text = "Je n’ai pas encore l’information complète. Pouvez-vous me préciser ce point pour que je puisse avancer ?"

        if not assistant_text.startswith("[FORMAT:message]"):
            assistant_text = f"[FORMAT:message]\n\n{assistant_text}"

        assistant_meta = (result or {}).get("message_metadata") or (result or {}).get("route_contract") or {
            "event_type": "backend_chat"
        }

        persisted = await _insert_seek_infos_assistant_message(
            conn,
            conversation_id=str(conversation_id),
            public_user_id=str(public_user_id),
            user_message_id=str(user_message_id),
            reply_text=assistant_text,
            assistant_meta=assistant_meta,
        )

        yield {
            "type": "done",
            "seek_infos_followup_detected": True,
            "seek_infos_result": result,
            "assistant_message": {
                "id": persisted["assistant_message_id"],
                "sent_at": persisted["sent_at"],
                "content": persisted["content"],
            },
            "provider": {
                "primary": (
                    ((assistant_meta or {}).get("provider") or {}).get("primary")
                    if isinstance(assistant_meta, dict)
                    else "seek_infos_followup"
                ) or "seek_infos_followup",
                "fallback_used": False,
            },
        }

        return

    llm = LLMRuntime()

    ctx = await load_context_light(
        conn=conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    chat_logger.info(
        "chat.routing.mode",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        mode="normal_run_only",
        seek_infos_active=False,
    )

    orchestrator = OrchestratorAgent(llm)

    try:
        orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)
        _hydrate_orch_brain_fields(orch)

    except Exception as e:
        chat_logger.error(
            "chat.orchestrator.error",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            error_type=type(e).__name__,
            error=str(e)[:240],
            exc_info=True,
        )
        raise

    executor = PlanExecutor(
        conn=conn,
        llm=llm,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
        user_message=str(msg["content"]),
    )

    final_answer = None
    exec_final_debug = {}
    exec_provider_primary = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider") or "orchestrated"

    async for ev in executor.run_stream(plan=orch.plan):
        etype = ev.get("type")

        if etype == "delta":
            yield {
                "type": "delta",
                "text": str(ev.get("text") or ""),
            }
            continue

        if etype == "escalate":
            reason = str(ev.get("reason") or "").strip().lower()

            chat_logger.info(
                "chat.orchestrator.escalate_rerun",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                reason=reason,
            )

            async for rerun_ev in _rerun_after_escalation(
                reason=reason,
                ctx=ctx,
                orchestrator=orchestrator,
                msg=msg,
                conn=conn,
                llm=llm,
                public_user_id=str(public_user_id),
                conversation_id=str(conversation_id),
            ):
                if rerun_ev.get("type") == "delta":
                    yield rerun_ev
                    continue

                if rerun_ev.get("type") == "result":
                    if rerun_ev.get("error_event"):
                        yield rerun_ev["error_event"]
                        return

                    orch = rerun_ev["orch"]
                    final_answer = rerun_ev["final_answer"]
                    exec_final_debug = rerun_ev["exec_final_debug"]
                    exec_provider_primary = rerun_ev["exec_provider_primary"]
                    break

            break

        if etype == "error":
            yield ev
            return

        if etype == "final":
            final_answer = ev.get("answer") or SAFE_FALLBACK_ANSWER
            exec_final_debug = ev.get("debug") or {}

    reply_text_raw = final_answer or SAFE_FALLBACK_ANSWER
    reply_text, flags = extract_and_clean_message_flags(reply_text_raw)

    provider = {
        "primary": exec_provider_primary,
        "fallback_used": (orch.ok is False),
        "orchestrator": {"provider": (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider")},
        "flags": flags.to_metadata(),
        "stream_debug": exec_final_debug,
    }


    persisted = await _insert_or_update_assistant_message(
        conn,
        conversation_id=str(conversation_id),
        public_user_id=str(public_user_id),
        user_message_id=str(user_message_id),
        reply_text=reply_text,
        provider=provider,
        orch=orch,
    )

    await _postprocess_assistant_message(
        conn,
        public_user_id=str(public_user_id),
        ctx=ctx,
        provider=provider,
        msg=msg,
        reply_text=reply_text,
        orch=orch,
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        assistant_message_id=str(persisted["assistant_message_id"]),
    )

    yield {
        "type": "done",
        "assistant_message": {
            "id": persisted["assistant_message_id"],
            "sent_at": persisted["sent_at"],
            "content": reply_text,
        },
        "provider": provider,
    }

async def handle_chat_message(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
) -> dict:
    last_done_event = None
    last_error_event = None

    async for event in handle_chat_message_stream(
        conn,
        conversation_id=conversation_id,
        user_message_id=user_message_id,
        auth_user_id=auth_user_id,
    ):
        etype = event.get("type")

        if etype == "done":
            last_done_event = event

        elif etype == "error":
            last_error_event = event

    if last_done_event:
        return {
            "ok": True,
            "assistant_message": last_done_event.get("assistant_message"),
            "provider": last_done_event.get("provider") or {
                "primary": "unknown",
                "fallback_used": False,
            },
        }

    if last_error_event:
        raise ChatError(
            str(last_error_event.get("message") or last_error_event.get("error") or "CHAT_STREAM_ERROR")
        )

    raise ChatError("CHAT_STREAM_ENDED_WITHOUT_DONE")