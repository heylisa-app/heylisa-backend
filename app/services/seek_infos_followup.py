#app/services/seek_infos_followup.py

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from datetime import date, datetime
from typing import Any, Dict
from uuid import UUID

from asyncpg import Connection

from app.core.chat_logger import chat_logger
from app.integrations.n8n_seek_infos_analyzer import fire_seek_infos_analyzer_webhook
from app.llm.runtime import LLMRuntime
from app.agents.response_writer import ResponseWriterAgent
from app.services.context_loader_v2 import load_context_light


def _json_safe(value):
    if value is None:
        return None

    if isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, UUID):
        return str(value)

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]

    try:
        json.dumps(value)
        return value
    except Exception:
        return str(value)


def _build_seek_infos_runtime_context(
    *,
    base_ctx: Dict[str, Any],
    seek_infos_context: Dict[str, Any],
    seek_request: Dict[str, Any],
    user_message: Dict[str, Any],
) -> Dict[str, Any]:
    ctx = deepcopy(base_ctx or {})

    runtime_block = ctx.get("runtime") or {}
    if not isinstance(runtime_block, dict):
        runtime_block = {}

    seek_block = {
        "mode": "seek_infos_active",
        "queue_id": seek_infos_context.get("queue_id"),
        "seek_request_id": seek_infos_context.get("seek_request_id"),
        "interaction_id": seek_infos_context.get("interaction_id"),
        "assistant_message_id": seek_infos_context.get("assistant_message_id"),
        "assistant_sent_at": seek_infos_context.get("assistant_sent_at"),
        "assistant_content": seek_infos_context.get("assistant_content"),
        "user_message_id": user_message.get("id"),
        "user_message_content": user_message.get("content"),
        "request": seek_request,
    }

    runtime_block["seek_infos"] = seek_block
    ctx["runtime"] = runtime_block
    ctx["seek_infos"] = seek_block

    return ctx


def _build_seek_infos_chat_system_prompt() -> str:
    return """Tu es Lisa, secrétaire médicale IA du cabinet.

Tu réponds DANS LE CHAT interne du cabinet quand un échange de type SEEK_INFOS est actif.

Ton rôle ici :
- continuer la conversation naturellement avec le médecin ou le secrétariat
- obtenir les informations manquantes pour débloquer la réponse au patient
- rester concise, claire et professionnelle
- ne jamais inventer une information
- ne jamais prétendre avoir accès à un outil si ce n’est pas explicitement indiqué
- relancer intelligemment si la réponse du user est ambiguë, incomplète, trop brève ou hors sujet
- si le user change complètement de sujet, tu ne le forces pas brutalement à revenir, mais tu peux reformuler poliment ce qui manque si c’est pertinent

Style attendu :
- ton professionnel, simple, humain
- français naturel
- une réponse courte à moyenne
- pas de JSON
- pas de markdown technique
- pas d’explication de raisonnement

Important :
- tu réponds au dernier message user DANS le fil de conversation
- tu pilotes l’échange seek_infos tant qu’il reste actif
- tu aides à obtenir les infos concrètes nécessaires
"""


def _build_seek_infos_chat_user_prompt(
    *,
    assistant_text: str | None,
    user_text: str | None,
    seek_request: Dict[str, Any],
    seek_infos_context: Dict[str, Any],
) -> str:
    tasks = seek_request.get("tasks") or []
    missing_items = seek_request.get("missing_items") or []
    title = seek_request.get("title")
    reason = seek_request.get("reason")
    target_role = seek_request.get("target_role")
    priority = seek_request.get("priority")

    return f"""
Tu dois répondre au dernier message du user dans une conversation interne liée à un SEEK_INFOS.

=== MESSAGE LISA PRÉCÉDENT ===
{assistant_text or ""}

=== DERNIER MESSAGE USER ===
{user_text or ""}

=== DEMANDE SEEK_INFOS ACTIVE ===
Titre : {title or ""}
Raison : {reason or ""}
Cible : {target_role or ""}
Priorité : {priority or ""}

Tâches attendues :
{json.dumps(tasks, ensure_ascii=False, indent=2)}

Éléments encore manquants :
{json.dumps(missing_items, ensure_ascii=False, indent=2)}

=== CONTEXTE TECHNIQUE ===
{json.dumps(_json_safe(seek_infos_context), ensure_ascii=False, indent=2)}

=== TA MISSION ===
Réponds dans le chat de manière naturelle et utile.

Si le message du user est ambigu, incomplet ou trop bref, relance-le proprement pour obtenir les informations manquantes.
Si le message répond partiellement, accuse réception brièvement puis demande exactement ce qu’il manque encore.
Si tout semble clair, reformule brièvement la compréhension et confirme que tu peux avancer.

Ne réponds qu’avec le message final à envoyer dans le chat.
""".strip()

def _build_seek_infos_route_contract(
    *,
    seek_infos_context: Dict[str, Any],
    llm_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    seek_request_id = str(seek_infos_context.get("seek_request_id") or "").strip()
    queue_id = str(seek_infos_context.get("queue_id") or "").strip()
    interaction_id = str(seek_infos_context.get("interaction_id") or "").strip()

    # ⚠️ identifiant de reprise local, pas un vrai conversation_loops.id
    resume_loop_id = seek_request_id or queue_id or interaction_id or "seek_infos_active"

    provider_name = ""
    provider_model = ""
    provider_duration_ms = None

    if llm_meta and isinstance(llm_meta, dict):
        provider_name = str(llm_meta.get("provider") or "").strip()
        provider_model = str(llm_meta.get("model") or "").strip()
        provider_duration_ms = llm_meta.get("duration_ms")

    return {
        # -----------------------------
        # Compat détecteur actuel
        # -----------------------------
        "event_type": "lisa_proactive_message",
        "proactive_kind": "seek_infos",
        "awaiting_internal_reply": True,
        "queue_id": queue_id or None,
        "seek_request_id": seek_request_id or None,
        "interaction_id": interaction_id or None,

        # -----------------------------
        # Contrat standard normalisé
        # -----------------------------
        "orch": {
            "mode": "loop",
            "need_web": False,
            "confidence": 1.0,
            "intent_final": "seek_infos_followup",
        },
        "brain": {
            "intent": "seek_infos_followup",
            "brain_key": "seek_infos_followup",
            "runtime_state": "seek_infos_active",
            "resume_loop_id": resume_loop_id,
            "keep_warm_topic": True,
            "primary_brain_key": "seek_infos_followup",
            "secondary_brain_key": "cabinet_assistance",
            "secondary_brain_reason": "seek_infos_active_context",
        },
        "provider": {
            "flags": {
                "aha_moment": False,
                "aha_request": False,
                "custom_request": False,
                "trial_feedback": False,
                "discovery_abort": False,
                "task_to_execute": False,
            },
            "primary": provider_name,
            "orchestrator": {
                "provider": "seek_infos_followup",
            },
            "stream_debug": {
                "provider": {
                    "model": provider_model,
                    "provider": provider_name,
                },
                "node_outputs": {},
                "response_writer": {
                    "model": provider_model,
                    "intent": "seek_infos_followup",
                    "need_web": False,
                    "provider": provider_name,
                    "duration_ms": provider_duration_ms,
                },
            },
            "fallback_used": False,
        },
        "seek_infos": {
            "queue_id": queue_id or None,
            "seek_request_id": seek_request_id or None,
            "interaction_id": interaction_id or None,
            "awaiting_internal_reply": True,
        },
    }


async def handle_seek_infos_followup(
    conn: Connection,
    *,
    conversation_id: str,
    user_message_id: str,
    public_user_id: str,
    seek_infos_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Handler V3 :
    - routing seek_infos
    - déclenchement webhook n8n
    - génération immédiate d'une vraie réponse Lisa dans le chat
    """

    user_row = await conn.fetchrow(
        """
        select id, content, created_at, metadata
        from public.conversation_messages
        where id = $1::uuid
        limit 1
        """,
        user_message_id,
    )
    user_message = _json_safe(dict(user_row)) if user_row else {}

    seek_request_id = seek_infos_context.get("seek_request_id")
    seek_request_row = None
    if seek_request_id:
        seek_request_row = await conn.fetchrow(
            """
            select
              id,
              cabinet_id,
              queue_id,
              interaction_id,
              source_message_id,
              source_thread_id,
              source_ref,
              target_role,
              channel,
              request_kind,
              status,
              priority,
              title,
              reason,
              tasks,
              missing_items,
              asked_at,
              due_at,
              answered_at,
              escalated_at,
              last_reminded_at,
              answer_payload,
              metadata,
              created_at,
              updated_at
            from public.cabinet_info_requests
            where id = $1::uuid
            limit 1
            """,
            seek_request_id,
        )

    seek_request = _json_safe(dict(seek_request_row)) if seek_request_row else {}

    payload = _json_safe({
        "source": "backend_seek_infos_followup",
        "schema_version": "v1",
        "conversation_id": str(conversation_id),
        "public_user_id": str(public_user_id),
        "user_message_id": str(user_message_id),
        "queue_id": seek_infos_context.get("queue_id"),
        "seek_request_id": seek_infos_context.get("seek_request_id"),
        "interaction_id": seek_infos_context.get("interaction_id"),
        "assistant_message_id": seek_infos_context.get("assistant_message_id"),
        "assistant_sent_at": seek_infos_context.get("assistant_sent_at"),
        "assistant_text": seek_infos_context.get("assistant_content"),
        "user_text": str(user_message.get("content") or ""),
        "seek_infos_context": seek_infos_context,
        "seek_request": seek_request,
    })

    try:
        asyncio.create_task(fire_seek_infos_analyzer_webhook(payload))
        chat_logger.info(
            "seek_infos_analyzer.hook.task_scheduled",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            public_user_id=str(public_user_id),
            queue_id=seek_infos_context.get("queue_id"),
            seek_request_id=seek_infos_context.get("seek_request_id"),
            interaction_id=seek_infos_context.get("interaction_id"),
        )
    except Exception as e:
        chat_logger.info(
            "seek_infos_analyzer.hook.schedule_error",
            conversation_id=str(conversation_id),
            user_message_id=str(user_message_id),
            error=str(e)[:180],
        )

    base_ctx = await load_context_light(
        conn=conn,
        public_user_id=str(public_user_id),
        conversation_id=str(conversation_id),
    )

    ctx = _build_seek_infos_runtime_context(
        base_ctx=base_ctx or {},
        seek_infos_context=seek_infos_context,
        seek_request=seek_request,
        user_message=user_message,
    )

    llm = LLMRuntime()
    rw = ResponseWriterAgent(llm)

    rw_result = await rw.run(
        user_message=str(user_message.get("content") or ""),
        raw_user_message=str(user_message.get("content") or ""),
        intent="seek_infos_followup",
        primary_brain_key="seek_infos_followup",
        secondary_brain_key="cabinet_assistance",
        secondary_brain_reason="seek_infos_active_context",
        resume_loop_id=str(
            seek_infos_context.get("seek_request_id")
            or seek_infos_context.get("queue_id")
            or seek_infos_context.get("interaction_id")
            or ""
        ),
        keep_warm_topic=True,
        language="fr",
        tone="warm",
        need_web=False,
        mode="normal",
        route_source="fastpath",
        runtime_state="seek_infos_active",
        context=ctx,
        quota={},
        web=None,
        web_search=None,
        docs_chunks=None,
        playbook=None,
    )

    assistant_text = str((rw_result or {}).get("answer") or "").strip()

    if not assistant_text:
        assistant_text = "Je n’ai pas encore l’information complète. Pouvez-vous me préciser ce point pour que je puisse avancer ?"

    route_contract = _build_seek_infos_route_contract(
        seek_infos_context=seek_infos_context,
        llm_meta=((rw_result or {}).get("debug") or {}),
    )

    return {
        "ok": True,
        "mode": "seek_infos_followup",
        "conversation": {
            "conversation_id": conversation_id,
            "public_user_id": public_user_id,
        },
        "seek_infos": {
            "queue_id": seek_infos_context.get("queue_id"),
            "seek_request_id": seek_infos_context.get("seek_request_id"),
            "interaction_id": seek_infos_context.get("interaction_id"),
            "assistant_message_id": seek_infos_context.get("assistant_message_id"),
        },
        "user_message": {
            "id": str(user_message.get("id")) if user_message.get("id") else None,
            "content": str(user_message.get("content") or ""),
        },
        "assistant_text": assistant_text,
        "route_contract": route_contract,
        "message_metadata": route_contract,
        "webhook_dispatched": True,
        "next_step": "n8n_seek_infos_analyzer",
        "logs": {
            "step": "seek_infos_followup_handler_v5",
            "ok": True,
            "resume_loop_id": route_contract.get("brain", {}).get("resume_loop_id"),
            "primary_brain_key": route_contract.get("brain", {}).get("primary_brain_key"),
        },
    }