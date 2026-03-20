# app/services/context_loader.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from asyncpg import Connection


def _meta_to_dict(meta: Any) -> Optional[Dict[str, Any]]:
    if meta is None:
        return None
    if isinstance(meta, dict):
        return meta
    if isinstance(meta, str):
        try:
            out = json.loads(meta)
            return out if isinstance(out, dict) else None
        except Exception:
            return None
    return None


async def load_context_light(conn: Connection, public_user_id: str, conversation_id: str) -> dict:
    # ---------------------------------------------------
    # 1) User minimal (aucune colonne legacy)
    # ---------------------------------------------------
    user_row = await conn.fetchrow(
        """
        select
          id,
          first_name,
          last_name,
          full_name,
          primary_company_id
        from public.users
        where id = $1::uuid
        """,
        public_user_id,
    )

    user = dict(user_row) if user_row else {
        "id": public_user_id,
        "first_name": None,
        "last_name": None,
        "full_name": None,
        "primary_company_id": None,
    }

    # ---------------------------------------------------
    # 2) Settings hardcodés minimalistes
    # ---------------------------------------------------
    settings = {
        "locale_main": "fr-FR",
        "timezone": "Europe/Paris",
        "use_tu_form": None,
        "discovery_status": "to_do",
    }

    # ---------------------------------------------------
    # 3) 30 derniers messages
    # ---------------------------------------------------
    rows = await conn.fetch(
        """
        select
          id,
          role,
          content,
          sent_at,
          metadata
        from public.conversation_messages
        where conversation_id = $1::uuid
        order by sent_at desc, id desc
        limit 30
        """,
        conversation_id,
    )

    rows = list(reversed(rows))

    messages: List[Dict[str, Any]] = []

    for r0 in rows:
        r = dict(r0)
        role = "assistant" if r.get("role") == "assistant" else "user"
        meta = _meta_to_dict(r.get("metadata"))

        intent_final = None
        mode = None
        need_web = None

        if isinstance(meta, dict):
            orch = meta.get("orch")
            if isinstance(orch, dict):
                intent_final = orch.get("intent_final")
                mode = orch.get("mode")
                need_web = orch.get("need_web")

        sent_at = r.get("sent_at")

        messages.append(
            {
                "role": role,
                "content": r.get("content"),
                "sent_at": sent_at.isoformat() if sent_at else None,
                "intent_final": intent_final,
                "mode": mode,
                "need_web": need_web,
            }
        )

    # ---------------------------------------------------
    # 4) Helpers historiques
    # ---------------------------------------------------
    last_user_message = None
    last_assistant_message = None
    last_assistant_intent = None
    last_assistant_mode = None

    for m in reversed(messages):
        if m.get("role") == "user" and last_user_message is None:
            last_user_message = m.get("content")

        if m.get("role") == "assistant" and last_assistant_message is None:
            last_assistant_message = m.get("content")
            last_assistant_intent = m.get("intent_final")
            last_assistant_mode = m.get("mode")

        if last_user_message is not None and last_assistant_message is not None:
            break

    user_messages_count = sum(1 for m in messages if m.get("role") == "user")

    # ---------------------------------------------------
    # 5) Structure neutre compatible pipeline
    # ---------------------------------------------------
    user_status = {
        "is_pro": False,
        "free_quota_used": 0,
        "free_quota_limit": 999,
        "state": "normal",
    }

    gates = {
        "smalltalk_intro_eligible": False,
        "smalltalk_target_key": None,
        "missing_required": [],
        "keyfacts_remaining": 0,
        "discovery_status": "to_do",
        "discovery_forced": False,
        "user_messages_count": int(user_messages_count),
        "smalltalk_done_derived": True,
        "transition_window": False,
        "transition_reason": None,
    }

    action_state = {
        "active_agent_keys": [],
        "has_paid_agent": False,
        "can_action_request": False,
        "executable_actions": [],
        "action_required_integrations": {},
        "required_integrations": [],
        "connected_integrations": [],
    }

    capabilities = {
        "has_paid_agent": False,
        "can_action_request": False,
        "can_deep_work": True,
        "can_professional_request": False,
    }

    onboarding = {
        "row": None,
        "has_paid_active": False,
        "has_pro_mode_active": False,
        "connected_tools_count": 0,
        "has_any_tool_connected": False,
        "status": None,
        "pro_mode": False,
        "primary_agent_key": None,
    }

    docs = {
        "scopes_all": [],
        "scopes_count": 0,
    }

    facts_store = {
        "count": 0,
        "items": [],
        "keys": [],
    }

    history = {
        "messages": messages,
        "last_user_message": last_user_message,
        "last_assistant_message": last_assistant_message,
        "last_assistant_intent_final": last_assistant_intent,
        "last_assistant_mode": last_assistant_mode,
    }

    return {
        "user": {
            "id": str(user.get("id")) if user.get("id") else None,
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "full_name": user.get("full_name"),
            "primary_company_id": user.get("primary_company_id"),
        },
        "settings": settings,
        "messages": messages,
        "history": history,
        "user_status": user_status,
        "gates": gates,
        "action_state": action_state,
        "capabilities": capabilities,
        "onboarding": onboarding,
        "docs": docs,
        "facts_store": facts_store,
        "user_facts": {
            "required_keys": [],
            "known": [],
            "missing_required": [],
            "missing_required_count": 0,
        },
    }