# app/services/chat.py

import json
from asyncpg import Connection

from app.llm.runtime import LLMRuntime
from app.agents.orchestrator import OrchestratorAgent
from app.services.plan_executor import PlanExecutor
from app.services.context_loader_v2 import load_context_light, load_context_with_billing
from typing import AsyncIterator

from app.core.chat_logger import chat_logger
from app.integrations.n8n_userfacts import fire_userfact_webhook
from app.services.message_flags import extract_and_clean_message_flags
from app.services.intent_routing.state_resolver_v2 import resolve_state_v2
from app.services.intent_routing.gates import apply_gates
from app.services.onboarding_state import apply_onboarding_state
from app.llm.runtime import LLMCallError
from app.integrations.n8n_feedback_analysis import fire_feedback_analysis_webhook

SAFE_FALLBACK_ANSWER = "Désolé — je n’ai pas réussi à générer une réponse. Réessaie."
TRIAL_FEEDBACK_BILLING_ALLOWED = {
    "trial_active",
    "trial_contacted",
    "trial_expired_waiting_response",
    "suspended",
}

TRIAL_FEEDBACK_BILLING_BLOCKED = {
    "pending_payment",
    "active_paid",
    "grace_period",
    "closed",
}


def _is_trial_feedback_billing_compatible(billing_status: str | None) -> bool:
    s = str(billing_status or "").strip().lower()
    if not s:
        return False
    if s in TRIAL_FEEDBACK_BILLING_BLOCKED:
        return False
    return s in TRIAL_FEEDBACK_BILLING_ALLOWED

def _compute_trial_feedback_flags(ctx: dict) -> dict:
    billing_ctx = (ctx or {}).get("billing") or {}

    billing_status = str(billing_ctx.get("billing_status") or "").strip().lower()
    billing_compatible = _is_trial_feedback_billing_compatible(billing_status)

    trial_feedback_context_active = bool(
        billing_ctx.get("trial_feedback_context_active") is True
    )
    trial_feedback_context_closed = bool(
        billing_ctx.get("trial_feedback_context_closed") is True
    )

    history_msgs = (((ctx or {}).get("history") or {}).get("messages") or [])
    if not isinstance(history_msgs, list):
        history_msgs = []

    last_lisa_contains_trial_phrase = False
    for m in reversed(history_msgs):
        if not isinstance(m, dict):
            continue

        sender_type = str(m.get("sender_type") or "").strip().lower()
        role = str(m.get("role") or "").strip().lower()
        content = str(m.get("content") or "")

        if sender_type == "lisa" or role == "assistant":
            if "fin de ma période d’essai" in content.lower():
                last_lisa_contains_trial_phrase = True
            break

    # ouverture conversationnelle si déjà active en DB
    # ou si le dernier message Lisa a explicitement ouvert le sujet
    conversation_trial_open = bool(
        trial_feedback_context_active or last_lisa_contains_trial_phrase
    )

    # fermeture définitive : si le contexte est closed en DB, terminé pour toujours
    # ou si billing est devenu incompatible ET qu'on avait déjà ouvert ce sujet
    permanently_closed = bool(
        trial_feedback_context_closed
        or (conversation_trial_open and not billing_compatible)
    )

    trial_feedback_active = bool(
        conversation_trial_open
        and not permanently_closed
        and billing_compatible
    )

    return {
        "billing_status": billing_status,
        "billing_compatible": billing_compatible,
        "trial_feedback_context_active": trial_feedback_context_active,
        "trial_feedback_context_closed": trial_feedback_context_closed,
        "last_lisa_contains_trial_phrase": last_lisa_contains_trial_phrase,
        "conversation_trial_open": conversation_trial_open,
        "permanently_closed": permanently_closed,
        "trial_feedback_active": trial_feedback_active,
    }

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

TRIAL_FEEDBACK_KEYPHRASE = "fin de ma période d’essai"


async def _get_last_lisa_message(conn: Connection, conversation_id: str):
    return await conn.fetchrow(
        """
        select id, content, sent_at, metadata
        from public.conversation_messages
        where conversation_id = $1::uuid
          and sender_type = 'lisa'
          and role = 'assistant'
        order by sent_at desc, id desc
        limit 1
        """,
        conversation_id,
    )


async def _get_billing_status(conn: Connection, public_user_id: str):
    return await conn.fetchrow(
        """
        select billing_status, billing_substatus
        from public.user_billing_status
        where public_user_id = $1::uuid
        limit 1
        """,
        public_user_id,
    )


async def _compute_trial_feedback_flag(
    conn: Connection,
    *,
    conversation_id: str,
    public_user_id: str,
) -> dict:
    last_lisa_msg = await _get_last_lisa_message(conn, conversation_id)
    billing_row = await _get_billing_status(conn, public_user_id)

    last_lisa_content = str((last_lisa_msg["content"] if last_lisa_msg else "") or "")
    billing_status = str((billing_row["billing_status"] if billing_row else "") or "").strip()
    billing_substatus = str((billing_row["billing_substatus"] if billing_row else "") or "").strip()

    last_lisa_contains_trial_phrase = TRIAL_FEEDBACK_KEYPHRASE in last_lisa_content

    billing_keeps_trial_feedback_active = billing_status in {
        "trial_contacted",
        "trial_expired_waiting_response",
        "pending_payment",
    }

    trial_feedback_active = (
        last_lisa_contains_trial_phrase
        or billing_keeps_trial_feedback_active
    )

    return {
        "trial_feedback_active": trial_feedback_active,
        "last_lisa_contains_trial_phrase": last_lisa_contains_trial_phrase,
        "billing_status": billing_status or None,
        "billing_substatus": billing_substatus or None,
    }

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

    mode = None
    try:
        for n in (orch.plan or {}).get("nodes", []):
            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                mode = ((n.get("inputs") or {}) if isinstance(n.get("inputs"), dict) else {}).get("mode")
                break
    except Exception:
        mode = None

    intent_final = None
    try:
        dbg = getattr(orch, "debug", None)
        if isinstance(dbg, dict):
            intent_final = dbg.get("intent_final") or dbg.get("intent")
    except Exception:
        intent_final = None

    if not intent_final:
        intent_final = getattr(orch, "intent", None)

    assistant_meta = {
        "event_type": "backend_chat",
        "provider": provider,
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


async def _postprocess_assistant_message(
    conn: Connection,
    *,
    public_user_id: str,
    ctx: dict,
    provider: dict,
    msg,
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
        trial_feedback = bool(provider_flags.get("trial_feedback") is True)

        if trial_feedback:
            payload = {
                "source": "chat_trial_feedback",
                "public_user_id": str(public_user_id),
                "conversation_id": str(conversation_id),
                "conversation_channel": ((ctx or {}).get("conversation") or {}).get("channel"),
                "user_message_id": str(user_message_id),
                "assistant_message_id": str(assistant_message_id),
                "user_text": (msg["content"] or ""),
                "assistant_text": "",  # volontairement vide ici, comme userfacts minimal
                "cabinet_account_id": ((ctx or {}).get("cabinet") or {}).get("id"),
                "member_role": ((ctx or {}).get("member") or {}).get("role"),
                "member_job_role": ((ctx or {}).get("member") or {}).get("job_role"),
                "billing_status": ((ctx or {}).get("conversation_flags") or {}).get("billing_status"),
                "billing_substatus": ((ctx or {}).get("conversation_flags") or {}).get("billing_substatus"),
                "trial_feedback_active": ((ctx or {}).get("conversation_flags") or {}).get("trial_feedback_active"),
            }

            chat_logger.info(
                "feedback_analysis.hook.payload_ready",
                public_user_id=str(public_user_id),
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                assistant_message_id=str(assistant_message_id),
            )

            import asyncio
            asyncio.create_task(fire_feedback_analysis_webhook(payload))

            chat_logger.info("feedback_analysis.hook.task_scheduled")

    except Exception as e:
        chat_logger.info("feedback_analysis.webhook.call_error", error=str(e)[:180])


async def _persist_onboarding_flags(
    conn: Connection,
    *,
    public_user_id: str,
    flags_meta: dict,
) -> None:
    """
    Source de vérité unique pour la progression onboarding/discovery.
    Écrit uniquement dans public.user_onboarding_state.
    """
    try:
        if not isinstance(flags_meta, dict):
            chat_logger.info(
                "chat.onboarding.flags.skipped_invalid",
                public_user_id=str(public_user_id),
                flags_type=str(type(flags_meta)),
            )
            return

        chat_logger.info(
            "chat.onboarding.flags.received",
            public_user_id=str(public_user_id),
            aha_request=bool(flags_meta.get("aha_request")),
            aha_moment=bool(flags_meta.get("aha_moment")),
            discovery_abort=bool(flags_meta.get("discovery_abort")),
            flags_meta=flags_meta,
        )

        if flags_meta.get("aha_request") is True:
            updated_user_id = await conn.fetchval(
                """
                update public.user_onboarding_state
                set discovery_status = 'pending',
                    updated_at = now()
                where user_id = $1::uuid
                  and coalesce(discovery_status, 'to_do') in ('to_do', '')
                returning user_id
                """,
                public_user_id,
            )

            row = await conn.fetchrow(
                """
                select
                    user_id,
                    discovery_status,
                    discovery_completed_at,
                    updated_at
                from public.user_onboarding_state
                where user_id = $1::uuid
                limit 1
                """,
                public_user_id,
            )

            chat_logger.info(
                "chat.onboarding.flags.aha_request_applied",
                public_user_id=str(public_user_id),
                updated=bool(updated_user_id),
                row=dict(row) if row else None,
            )

        if flags_meta.get("aha_moment") is True:
            updated_user_id = await conn.fetchval(
                """
                update public.user_onboarding_state
                set discovery_status = 'complete',
                    discovery_completed_at = now(),
                    updated_at = now()
                where user_id = $1::uuid
                returning user_id
                """,
                public_user_id,
            )

            row = await conn.fetchrow(
                """
                select
                    user_id,
                    discovery_status,
                    discovery_completed_at,
                    updated_at
                from public.user_onboarding_state
                where user_id = $1::uuid
                limit 1
                """,
                public_user_id,
            )

            chat_logger.info(
                "chat.onboarding.flags.aha_moment_applied",
                public_user_id=str(public_user_id),
                updated=bool(updated_user_id),
                row=dict(row) if row else None,
            )

        elif flags_meta.get("discovery_abort") is True:
            updated_user_id = await conn.fetchval(
                """
                update public.user_onboarding_state
                set discovery_status = 'aborted',
                    updated_at = now()
                where user_id = $1::uuid
                  and coalesce(discovery_status, 'pending') <> 'complete'
                returning user_id
                """,
                public_user_id,
            )

            row = await conn.fetchrow(
                """
                select
                    user_id,
                    discovery_status,
                    discovery_completed_at,
                    updated_at
                from public.user_onboarding_state
                where user_id = $1::uuid
                limit 1
                """,
                public_user_id,
            )

            chat_logger.info(
                "chat.onboarding.flags.discovery_abort_applied",
                public_user_id=str(public_user_id),
                updated=bool(updated_user_id),
                row=dict(row) if row else None,
            )

    except Exception as e:
        chat_logger.info(
            "chat.onboarding.flags.persist_error",
            public_user_id=str(public_user_id),
            error=str(e)[:180],
        )


def _pick_discovery_doc_scopes(ctx: dict) -> list[str]:
    """
    V2 :
    discovery_capabilities charge obligatoirement la doc médicale métier.
    """
    return ["discovery.medical_assistant"]

def _build_failsafe_light_plan(*, ctx: dict, state_decision, soft_paywall_warning: bool) -> dict:
    """
    Plan minimal: charge contexte light puis ResponseWriter.
    Aucun playbook/docs chunks => prompt ultra light.
    """
    language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
    forced_state = str(getattr(state_decision, "state", "") or "normal")

    nodes = [
        {
            "id": "A",
            "type": "tool.db_load_context",
            "parallel_group": "P1",
            "inputs": {"level": "light"},
        },
        {
            "id": "D",
            "type": "agent.response_writer",
            "depends_on": ["A"],
            "inputs": {
                "intent": "",                     # pas d'overlay intent
                "mode": forced_state,             # state = mode
                "route_source": "failsafe",       # traçable
                "runtime_state": forced_state,    # source de vérité RW
                "state": forced_state,            # idem
                "language": language,
                "tone": "warm",
                "need_web": False,
                "soft_paywall_warning": bool(soft_paywall_warning),
                "transition_window": bool(getattr(state_decision, "transition_window", False)),
                "transition_reason": getattr(state_decision, "transition_reason", None),
                "smalltalk_target_key": ((ctx or {}).get("gates") or {}).get("smalltalk_target_key"),
            },
        },
    ]
    return {"nodes": nodes}

async def handle_chat_message_stream(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    auth_user_id: str | None,
) -> AsyncIterator[dict]:
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
            yield {
                "type": "done",
                "assistant_message": {
                    "id": str(existing["id"]),
                    "sent_at": existing["sent_at"].isoformat(),
                    "content": existing["content"],
                },
                "provider": {"primary": "cache", "fallback_used": False},
            }
            return

    llm = LLMRuntime()
    provider = {"primary": "unknown", "fallback_used": False}

    ctx = await load_context_with_billing(
        conn=conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    chat_logger.info(
        "chat.billing.ctx_loaded",
        conversation_id=str(conversation_id),
        public_user_id=str(public_user_id),
        has_billing=bool((ctx or {}).get("billing")),
        billing_status=((ctx or {}).get("billing") or {}).get("billing_status"),
        trial_feedback_context_active=((ctx or {}).get("billing") or {}).get("trial_feedback_context_active"),
        trial_feedback_context_closed=((ctx or {}).get("billing") or {}).get("trial_feedback_context_closed"),
    )

    onboarding_result = await apply_onboarding_state(
        conn=conn,
        ctx=ctx,
        public_user_id=str(public_user_id),
        is_user_message=True,
    )
    ctx["onboarding_runtime"] = onboarding_result

    trial_flags = _compute_trial_feedback_flags(ctx or {})

    ctx.setdefault("gates", {})
    ctx["gates"]["trial_feedback_active"] = trial_flags["trial_feedback_active"]
    ctx["gates"]["last_lisa_contains_trial_phrase"] = trial_flags["last_lisa_contains_trial_phrase"]
    ctx["gates"]["billing_status"] = trial_flags["billing_status"]
    ctx["gates"]["billing_compatible_for_trial_feedback"] = trial_flags["billing_compatible"]
    ctx["gates"]["trial_feedback_context_active"] = trial_flags["trial_feedback_context_active"]
    ctx["gates"]["trial_feedback_context_closed"] = trial_flags["trial_feedback_context_closed"]
    ctx["gates"]["trial_feedback_permanently_closed"] = trial_flags["permanently_closed"]

    chat_logger.info(
        "chat.trial_feedback.flags",
        conversation_id=str(conversation_id),
        public_user_id=str(public_user_id),
        trial_feedback_active=bool(trial_flags["trial_feedback_active"]),
        last_lisa_contains_trial_phrase=bool(trial_flags["last_lisa_contains_trial_phrase"]),
        billing_status=trial_flags["billing_status"],
        billing_compatible=bool(trial_flags["billing_compatible"]),
        trial_feedback_context_active=bool(trial_flags["trial_feedback_context_active"]),
        trial_feedback_context_closed=bool(trial_flags["trial_feedback_context_closed"]),
        trial_feedback_permanently_closed=bool(trial_flags["permanently_closed"]),
    )

    state_decision = resolve_state_v2(ctx=ctx or {})
    gates_decision = apply_gates(ctx=ctx or {})
    soft_paywall_warning = bool(gates_decision.get("soft_paywall_warning"))

    if bool(getattr(state_decision, "fastpath_allowed", False)) is True:
        language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
        intent = ""
        mode = str(getattr(state_decision, "state", "normal") or "normal")

        nodes = [
            {
                "id": "A",
                "type": "tool.db_load_context",
                "parallel_group": "P1",
                "inputs": {"level": "light"},
            },
        ]

        if state_decision.state == "discovery_capabilities":
            scopes = _pick_discovery_doc_scopes(ctx or {})
            nodes.append(
                {
                    "id": "S",
                    "type": "tool.docs_chunks",
                    "depends_on": ["A"],
                    "inputs": {"scopes": scopes},
                }
            )

        deps = ["A"] + (["S"] if state_decision.state == "discovery_capabilities" else [])

        nodes.append(
            {
                "id": "D",
                "type": "agent.response_writer",
                "depends_on": deps,
                "inputs": {
                    "intent": intent,
                    "mode": mode,
                    "route_source": "fastpath",
                    "runtime_state": str(state_decision.state),
                    "language": language,
                    "tone": "warm",
                    "need_web": False,
                    "soft_paywall_warning": soft_paywall_warning,
                    "transition_window": bool(getattr(state_decision, "transition_window", False)),
                    "transition_reason": getattr(state_decision, "transition_reason", None),
                    "smalltalk_target_key": ((ctx or {}).get("gates") or {}).get("smalltalk_target_key"),
                },
            }
        )

        plan = {"nodes": nodes}

        orch = type("OrchStub", (), {})()
        orch.ok = True
        orch.intent = intent
        orch.language = language
        orch.need_web = False
        orch.confidence = 1.0
        orch.plan = plan
        orch.debug = {
            "intent_final": intent,
            "mode": mode,
            "meta": {"provider": "fastpath"},
        }

    else:
        orchestrator = OrchestratorAgent(llm)

        try:
            orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)
        except Exception as e:
            chat_logger.error(
                "chat.orchestrator.failsafe_triggered",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                error_type=type(e).__name__,
                error=str(e)[:240],
                exc_info=True,
            )

            plan = _build_failsafe_light_plan(
                ctx=ctx or {},
                state_decision=state_decision,
                soft_paywall_warning=soft_paywall_warning,
            )

            orch = type("OrchStub", (), {})()
            orch.ok = False
            orch.intent = ""
            orch.language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
            orch.need_web = False
            orch.confidence = 0.0
            orch.plan = plan
            orch.debug = {
                "intent_final": "",
                "mode": str(getattr(state_decision, "state", "") or "normal"),
                "meta": {"provider": "failsafe"},
                "error_type": type(e).__name__,
            }

        try:
            forced_state = str(getattr(state_decision, "state", "") or "")
            if isinstance(getattr(orch, "plan", None), dict):
                for n in orch.plan.get("nodes", []):
                    if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                        inputs = n.get("inputs") or {}
                        if isinstance(inputs, dict):
                            inputs["route_source"] = "orchestrator"
                            inputs["runtime_state"] = forced_state
                            inputs["state"] = forced_state
                            inputs["soft_paywall_warning"] = soft_paywall_warning
                            inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                            inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                            n["inputs"] = inputs
        except Exception:
            pass

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

            if reason == "need_web":
                ctx.setdefault("gates", {})
                ctx["gates"]["force_need_web"] = True
            elif reason == "need_docs":
                ctx.setdefault("gates", {})
                ctx["gates"]["force_need_docs"] = True

            orchestrator = OrchestratorAgent(llm)
            ctx["runtime_state"] = {"state": str(getattr(state_decision, "state", "") or "")}
            orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

            try:
                if isinstance(getattr(orch, "plan", None), dict):
                    for n in orch.plan.get("nodes", []):
                        if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                            inputs = n.get("inputs") or {}
                            if isinstance(inputs, dict):
                                inputs["route_source"] = "orchestrator"
                                inputs["runtime_state"] = str(getattr(state_decision, "state", "") or "")
                                inputs["soft_paywall_warning"] = soft_paywall_warning
                                inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                                inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                                n["inputs"] = inputs
            except Exception:
                pass

            async for ev2 in executor.run_stream(plan=orch.plan):
                if ev2.get("type") == "delta":
                    yield {
                        "type": "delta",
                        "text": str(ev2.get("text") or ""),
                    }
                elif ev2.get("type") == "error":
                    yield ev2
                    return
                elif ev2.get("type") == "final":
                    final_answer = ev2.get("answer") or SAFE_FALLBACK_ANSWER
                    exec_final_debug = ev2.get("debug") or {}
                    exec_provider_primary = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider") or "orchestrated"
            continue

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

    await _persist_onboarding_flags(
        conn,
        public_user_id=str(public_user_id),
        flags_meta=flags.to_metadata(),
    )

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

    # 4) Routing start
    llm = LLMRuntime()
    provider = {"primary": "unknown", "fallback_used": False}

    chat_logger.info(
        "chat.routing.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )

    # 4bis) Load context (light) for routing (state_resolver + orchestrator)
    ctx = await load_context_with_billing(
        conn=conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    chat_logger.info(
        "chat.billing.ctx_loaded",
        conversation_id=str(conversation_id),
        public_user_id=str(public_user_id),
        has_billing=bool((ctx or {}).get("billing")),
        billing_status=((ctx or {}).get("billing") or {}).get("billing_status"),
        trial_feedback_context_active=((ctx or {}).get("billing") or {}).get("trial_feedback_context_active"),
        trial_feedback_context_closed=((ctx or {}).get("billing") or {}).get("trial_feedback_context_closed"),
    )

    # -------------------------------------------------
    # 🧭 APPLY ONBOARDING STATE (Approche A)
    # -------------------------------------------------

    onboarding_result = await apply_onboarding_state(
        conn=conn,
        ctx=ctx,
        public_user_id=str(public_user_id),
        is_user_message=True,
    )

    # injecte le résultat dans ctx pour le resolver
    ctx["onboarding_runtime"] = onboarding_result

    trial_flags = _compute_trial_feedback_flags(ctx or {})

    ctx.setdefault("gates", {})
    ctx["gates"]["trial_feedback_active"] = trial_flags["trial_feedback_active"]
    ctx["gates"]["last_lisa_contains_trial_phrase"] = trial_flags["last_lisa_contains_trial_phrase"]
    ctx["gates"]["billing_status"] = trial_flags["billing_status"]
    ctx["gates"]["billing_compatible_for_trial_feedback"] = trial_flags["billing_compatible"]
    ctx["gates"]["trial_feedback_context_active"] = trial_flags["trial_feedback_context_active"]
    ctx["gates"]["trial_feedback_context_closed"] = trial_flags["trial_feedback_context_closed"]
    ctx["gates"]["trial_feedback_permanently_closed"] = trial_flags["permanently_closed"]

    chat_logger.info(
        "chat.trial_feedback.flags",
        conversation_id=str(conversation_id),
        public_user_id=str(public_user_id),
        trial_feedback_active=bool(trial_flags["trial_feedback_active"]),
        last_lisa_contains_trial_phrase=bool(trial_flags["last_lisa_contains_trial_phrase"]),
        billing_status=trial_flags["billing_status"],
        billing_compatible=bool(trial_flags["billing_compatible"]),
        trial_feedback_context_active=bool(trial_flags["trial_feedback_context_active"]),
        trial_feedback_context_closed=bool(trial_flags["trial_feedback_context_closed"]),
        trial_feedback_permanently_closed=bool(trial_flags["permanently_closed"]),
    )

    chat_logger.info(
        "chat.ctx.loaded.v2",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        has_user=bool((ctx or {}).get("user")),
        has_member=bool((ctx or {}).get("member")),
        has_cabinet=bool((ctx or {}).get("cabinet")),
        cabinet_name=((ctx or {}).get("cabinet") or {}).get("name"),
        member_role=((ctx or {}).get("member") or {}).get("role"),
        member_job_role=((ctx or {}).get("member") or {}).get("job_role"),
        use_tu_form=((ctx or {}).get("preferences") or {}).get("use_tu_form"),
        preferred_name=((ctx or {}).get("preferences") or {}).get("preferred_name"),
        addressing_preference_known=((ctx or {}).get("preferences") or {}).get("addressing_preference_known"),
        user_facts_count=len((((ctx or {}).get("facts") or {}).get("user_facts") or []),
        ),
        cabinet_facts_count=len((((ctx or {}).get("facts") or {}).get("cabinet_facts") or []),
        ),
        last_messages_count=len((((ctx or {}).get("history") or {}).get("messages") or [])),
        intro_sent=bool(((ctx or {}).get("runtime") or {}).get("intro_sent")),
    )

    state_decision = resolve_state_v2(ctx=ctx or {})

    gates_decision = apply_gates(ctx=ctx or {})
    soft_paywall_warning = bool(gates_decision.get("soft_paywall_warning"))

    # -------------------------------------------------
    # 🧪 STATE DEBUG SNAPSHOT (source of truth inputs)
    # -------------------------------------------------
    try:
        user_status_ctx = (ctx or {}).get("user_status") or {}
        settings_ctx = (ctx or {}).get("settings") or {}
        gates_ctx = (ctx or {}).get("gates") or {}
        action_ctx = (ctx or {}).get("action_state") or {}
        onboarding_runtime = (ctx or {}).get("onboarding_runtime") or {}

        chat_logger.info(
            "chat.state.inputs_snapshot",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),

            # ABONNEMENT (DB truth)
            db_is_pro=bool(user_status_ctx.get("is_pro")),

            # QUOTA
            quota_state=str(user_status_ctx.get("state")),
            quota_used=int(user_status_ctx.get("free_quota_used") or 0),
            quota_limit=int(user_status_ctx.get("free_quota_limit") or 0),

            # DISCOVERY
            discovery_status=str(settings_ctx.get("discovery_status")),

            # SMALLTALK
            smalltalk_done=bool(gates_ctx.get("smalltalk_done_derived")),
            user_messages_count=int(gates_ctx.get("user_messages_count") or 0),

            # AGENTS
            active_agent_keys=action_ctx.get("active_agent_keys"),

            # ONBOARDING
            onboarding_active=bool(onboarding_runtime.get("active")),
            onboarding_target=str(onboarding_runtime.get("target")),

            # FINAL STATE DECISION
            resolved_state=str(getattr(state_decision, "state", "")),
        )
    except Exception:
        pass

    chat_logger.info(
        "chat.fastpath.decision",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        state=str(getattr(state_decision, "state", "")),
        fastpath_allowed=bool(getattr(state_decision, "fastpath_allowed", False)),
        soft_paywall_warning=soft_paywall_warning,
    )

    chat_logger.info(
        "chat.state_decision",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
        state=str(getattr(state_decision, "state", "")),
        fastpath_allowed=bool(getattr(state_decision, "fastpath_allowed", False)),
        soft_paywall_warning=soft_paywall_warning,
        transition_window=bool(getattr(state_decision, "transition_window", False)),
        transition_reason=str(getattr(state_decision, "transition_reason", "") or "")[:80],
    )

    # --- FASTPATH (v0) : smalltalk_intro / quota_blocked ---
    if bool(getattr(state_decision, "fastpath_allowed", False)) is True:
        language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"

        # FASTPATH = STATE ONLY (no intent overlay)
        intent = ""  # important: RW ignorera l'intent en fastpath (et même sans ça on n'en veut pas)
        mode = str(getattr(state_decision, "state", "normal") or "normal")

        chat_logger.info(
            "chat.fastpath.enter",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            state=str(state_decision.state),
            intent=str(intent),
            mode=str(mode),
        )

        nodes = [
            {
                "id": "A",
                "type": "tool.db_load_context",
                "parallel_group": "P1",
                "inputs": {"level": "light"},
            },
        ]

        # ✅ discovery_capabilities => docs_chunks obligatoire
        if state_decision.state == "discovery_capabilities":
            scopes = _pick_discovery_doc_scopes(ctx or {})
            chat_logger.info(
                "chat.discovery.docs_selected",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                scopes=scopes,
            )
            nodes.append(
                {
                    "id": "S",
                    "type": "tool.docs_chunks",
                    "depends_on": ["A"],
                    "inputs": {"scopes": scopes},
                }
            )

        # response writer
        deps = ["A"] + (["S"] if state_decision.state == "discovery_capabilities" else [])

        nodes.append(
            {
                "id": "D",
                "type": "agent.response_writer",
                "depends_on": deps,
                "inputs": {
                    "intent": intent,
                    "mode": mode,
                    "route_source": "fastpath",
                    "runtime_state": str(state_decision.state),
                    "language": language,
                    "tone": "warm",
                    "need_web": False,
                    "soft_paywall_warning": soft_paywall_warning,
                    "transition_window": bool(getattr(state_decision, "transition_window", False)),
                    "transition_reason": getattr(state_decision, "transition_reason", None),
                    "smalltalk_target_key": ((ctx or {}).get("gates") or {}).get("smalltalk_target_key"),
                },
            }
        )

        plan = {"nodes": nodes}

        orch = type("OrchStub", (), {})()
        orch.ok = True
        orch.intent = intent
        orch.language = language
        orch.need_web = False
        orch.confidence = 1.0
        orch.plan = plan
        orch.debug = {
            "intent_final": intent,
            "mode": mode,
            "meta": {"provider": "fastpath"},
            "state_decision": {
                "state": state_decision.state,
                "fastpath_allowed": state_decision.fastpath_allowed,
                "quota_blocked": getattr(state_decision, "quota_blocked", False),
                "soft_paywall_warning": getattr(state_decision, "soft_paywall_warning", False),
                "transition_window": getattr(state_decision, "transition_window", False),
            },
        }

    else:
        chat_logger.info(
            "chat.orchestrator.start",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
        )

        orchestrator = OrchestratorAgent(llm)

        try:
            orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

        except Exception as e:
            # ✅ FAIL-SAFE : on ne laisse jamais le chat crasher si l'orchestrator tombe
            chat_logger.error(
                "chat.orchestrator.failsafe_triggered",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                error_type=type(e).__name__,
                error=str(e)[:240],
                exc_info=True,
            )

            # Plan minimal RW (light)
            plan = _build_failsafe_light_plan(
                ctx=ctx or {},
                state_decision=state_decision,
                soft_paywall_warning=soft_paywall_warning,
            )

            # Stub orch compatible avec le reste du pipeline
            orch = type("OrchStub", (), {})()
            orch.ok = False
            orch.intent = ""
            orch.language = (((ctx or {}).get("settings") or {}).get("locale_main", "fr").split("-")[0]) or "fr"
            orch.need_web = False
            orch.confidence = 0.0
            orch.plan = plan
            orch.debug = {
                "intent_final": "",
                "mode": str(getattr(state_decision, "state", "") or "normal"),
                "meta": {"provider": "failsafe"},
                "error_type": type(e).__name__,
            }

        # Ensure route_source + FORCE runtime_state/state for ResponseWriter
        try:
            forced_state = str(getattr(state_decision, "state", "") or "")
            if isinstance(getattr(orch, "plan", None), dict):
                for n in orch.plan.get("nodes", []):
                    if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                        inputs = n.get("inputs") or {}
                        if isinstance(inputs, dict):
                            inputs["route_source"] = "orchestrator"
                            inputs["runtime_state"] = forced_state
                            inputs["state"] = forced_state
                            inputs["soft_paywall_warning"] = soft_paywall_warning
                            inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                            inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                            n["inputs"] = inputs
        except Exception:
            pass

        try:
            rw_inputs = None
            if isinstance(getattr(orch, "plan", None), dict):
                for n in orch.plan.get("nodes", []):
                    if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                        rw_inputs = n.get("inputs") or {}
                        break

            chat_logger.info(
                "chat.orchestrator.rw_inputs_after_patch",
                conversation_id=str(conversation_id),
                user_message_id=str(user_message_id),
                forced_state=str(getattr(state_decision, "state", "") or ""),
                rw_runtime_state=str((rw_inputs or {}).get("runtime_state") or ""),
                rw_state=str((rw_inputs or {}).get("state") or ""),
                rw_route_source=str((rw_inputs or {}).get("route_source") or ""),
                rw_intent=str((rw_inputs or {}).get("intent") or ""),
                rw_mode=str((rw_inputs or {}).get("mode") or ""),
            )
        except Exception:
            pass



    # 5) Execute plan (tools + response_writer)
    executor = PlanExecutor(
        conn=conn,
        llm=llm,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
        user_message=str(msg["content"]),
    )

    # V2 : aucun patch docs post-plan ici.
    # Les docs de discovery_capabilities sont injectées directement
    # au moment de la construction du fastpath.

    chat_logger.info(
        "chat.executor.start",
        conversation_id=str(conversation_id),
        user_message_id=str(user_message_id),
    )
    try:
        exec_out = await executor.run(plan=orch.plan)

        # --- Escalation handling ---
        orch_provider = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider")
        provider_primary = orch_provider or "orchestrated"

        if exec_out.get("escalate") is True:
            # ✅ On ne relance l’orchestrator QUE si on vient du fastpath
            if provider_primary == "fastpath":
                chat_logger.info(
                    "chat.fastpath.escalate_to_orchestrator",
                    conversation_id=str(conversation_id),
                    user_message_id=str(user_message_id),
                    reason=str(exec_out.get("escalate_reason") or "")[:120],
                )

                # --- Escalation hinting: force web/docs on orchestrator rerun (deterministic) ---
                try:
                    esc_reason = str(exec_out.get("escalate_reason") or "").strip().lower()

                    if not isinstance(ctx, dict):
                        ctx = {}

                    if not isinstance(ctx.get("gates"), dict):
                        ctx["gates"] = {}

                    if esc_reason == "need_web":
                        ctx["gates"]["force_need_web"] = True

                    if esc_reason == "need_docs":
                        ctx["gates"]["force_need_docs"] = True

                    chat_logger.info(
                        "chat.escalate.hint_applied",
                        conversation_id=str(conversation_id),
                        user_message_id=str(user_message_id),
                        esc_reason=esc_reason,
                        force_need_web=bool(ctx["gates"].get("force_need_web")),
                        force_need_docs=bool(ctx["gates"].get("force_need_docs")),
                    )
                except Exception:
                    pass

                orchestrator = OrchestratorAgent(llm)
                ctx = ctx or {}
                ctx["runtime_state"] = {"state": str(getattr(state_decision, "state", "") or "")}
                orch = await orchestrator.run(user_message=msg["content"], ctx=ctx)

                # patch plan: enforce route_source orchestrator
                try:
                    if isinstance(getattr(orch, "plan", None), dict):
                        for n in orch.plan.get("nodes", []):
                            if isinstance(n, dict) and n.get("type") == "agent.response_writer":
                                inputs = n.get("inputs") or {}
                                if isinstance(inputs, dict):
                                    inputs["route_source"] = "orchestrator"
                                    inputs["runtime_state"] = str(getattr(state_decision, "state", "") or "")
                                    inputs["soft_paywall_warning"] = soft_paywall_warning
                                    inputs["transition_window"] = bool(getattr(state_decision, "transition_window", False))
                                    inputs["transition_reason"] = getattr(state_decision, "transition_reason", None)
                                    n["inputs"] = inputs
                except Exception:
                    pass

                exec_out = await executor.run(plan=orch.plan)

            else:
                # ✅ sinon on ignore : un plan orchestré ne doit pas ré-escalader ici
                chat_logger.info(
                    "chat.escalate.ignored_non_fastpath",
                    conversation_id=str(conversation_id),
                    user_message_id=str(user_message_id),
                    provider_primary=str(provider_primary),
                    reason=str(exec_out.get("escalate_reason") or "")[:120],
                )

        reply_text_raw = exec_out.get("answer") or SAFE_FALLBACK_ANSWER

        # ✅ Nettoyage des flags de fin de message (aha_moment / discovery_abort)
        reply_text, flags = extract_and_clean_message_flags(reply_text_raw)

        orch_provider = (getattr(orch, "debug", {}) or {}).get("meta", {}).get("provider")
        provider_primary = orch_provider or "orchestrated"

        provider = {
            "primary": provider_primary,
            "fallback_used": (orch.ok is False),
            "orchestrator": {"provider": orch_provider},
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
        provider = {
            "primary": "error_fallback",
            "fallback_used": True,
            "error": str(e)[:160],
            "flags": {
                "aha_request": False,
                "aha_moment": False,
                "discovery_abort": False,
            },
        }

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

    await _persist_onboarding_flags(
        conn,
        public_user_id=str(public_user_id),
        flags_meta=provider.get("flags", {}) or {},
    )

    # 6bis) Fire-and-forget user facts catcher (must not impact chat latency)
    chat_logger.info("userfacts.hook.before", conversation_id=str(conversation_id), user_message_id=str(user_message_id))

    try:
        payload = {
            "source": "chat_message",
            "public_user_id": str(public_user_id),
            "conversation_id": str(conversation_id),
            "conversation_channel": ((ctx or {}).get("conversation") or {}).get("channel"),
            "user_message_id": str(user_message_id),
            "assistant_message_id": str(assistant_message_id),
            "user_text": (msg["content"] or ""),
            "assistant_text": reply_text,
            "locale": ((ctx or {}).get("settings") or {}).get("locale_main"),
            "timezone": ((ctx or {}).get("settings") or {}).get("timezone"),
            "cabinet_account_id": ((ctx or {}).get("cabinet") or {}).get("id"),
            "member_role": ((ctx or {}).get("member") or {}).get("role"),
            "member_job_role": ((ctx or {}).get("member") or {}).get("job_role"),
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