# app/services/context_loader.py
from __future__ import annotations
from typing import List, Dict, Any

from asyncpg import Connection
from app.services.smalltalk_state import compute_facts_status, compute_gates_status
from app.services.quota import get_quota_status
from datetime import datetime, timezone

import json
from typing import Any, Dict, Optional

def _meta_to_dict(meta: Any) -> Optional[Dict[str, Any]]:
    """
    Normalise metadata venant de Postgres/asyncpg.
    - dict => retourne dict
    - str (JSON) => parse
    - None / autre => None
    """
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
    # 1) user identity
    user = await conn.fetchrow(
        """
        select id, first_name, last_name, full_name
        from public.users
        where id = $1
        """,
        public_user_id,
    )

    # 2) settings (defaults if missing)
    settings_row = None
    try:
        settings_row = await conn.fetchrow(
            """
            select
                coalesce(locale_main, 'fr-FR') as locale_main,
                coalesce(timezone, 'UTC') as timezone,

                -- IMPORTANT: use_tu_form doit pouvoir rester NULL tant que non connu
                use_tu_form as use_tu_form,

                coalesce(intro_smalltalk_turns, 0) as intro_smalltalk_turns,
                coalesce(intro_smalltalk_done, false) as intro_smalltalk_done,
                coalesce(free_quota_limit, 8) as free_quota_limit,
                coalesce(free_quota_used, 0) as free_quota_used,
                coalesce(discovery_status, 'pending') as discovery_status,
                discovery_completed_at as discovery_completed_at,

                -- (si ces colonnes existent)
                main_city as main_city,
                main_activity as main_activity
            from public.user_settings
            where user_id = $1
            """,
            public_user_id,
        )
    except Exception:
        # Fallback si main_city / main_activity n'existent pas encore
        settings_row = await conn.fetchrow(
            """
            select
                coalesce(locale_main, 'fr-FR') as locale_main,
                coalesce(timezone, 'UTC') as timezone,

                use_tu_form as use_tu_form,

                coalesce(intro_smalltalk_turns, 0) as intro_smalltalk_turns,
                coalesce(intro_smalltalk_done, false) as intro_smalltalk_done,
                coalesce(free_quota_limit, 8) as free_quota_limit,
                coalesce(free_quota_used, 0) as free_quota_used,

                coalesce(discovery_status, 'pending') as discovery_status,
                discovery_completed_at as discovery_completed_at
            from public.user_settings
            where user_id = $1
            """,
            public_user_id,
        )

    if not settings_row:
        settings = {
            "locale_main": "fr-FR",
            "timezone": "UTC",
            "use_tu_form": None,  # <-- inconnu au départ

            "intro_smalltalk_turns": 0,
            "intro_smalltalk_done": False,

            "free_quota_limit": 8,
            "free_quota_used": 0,

            "discovery_status": "pending",
            "discovery_completed_at": None,

            "main_city": None,
            "main_activity": None,
        }
    else:
        settings = dict(settings_row)
        # normalise au cas où fallback query ne renvoie pas ces champs
        settings.setdefault("main_city", None)
        settings.setdefault("main_activity", None)
        settings.setdefault("use_tu_form", None)
        settings.setdefault("discovery_status", "pending")
        settings.setdefault("discovery_completed_at", None)

    # 3) last messages (10) for this conversation
    rows = await conn.fetch(
        """
        select role, content, sent_at, metadata
        from public.conversation_messages
        where conversation_id = $1
        order by sent_at desc, id desc
        limit 10
        """,
        conversation_id,
    )

    # we fetched DESC => reverse to get chronological order
    rows = list(reversed(rows))

    messages: List[Dict[str, Any]] = []

    for r0 in rows:
        # asyncpg.Record -> dict pour avoir .get + robustesse
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
                "sent_at": (sent_at.isoformat() if sent_at else None),

                # continuity hints (optionnels)
                "intent_final": intent_final,
                "mode": mode,
                "need_web": need_web,
            }
        )

    # 3bis) user_status (source of truth quota)
    qs = await get_quota_status(conn, str(public_user_id))
    user_status = {
        "is_pro": bool(qs.is_pro),
        "free_quota_used": int(qs.used),
        "free_quota_limit": int(qs.limit),
        "state": str(qs.state),  # normal | warn_last_free | blocked
    }

    # 4) facts + gates (smalltalk intro state)
    user_profile = dict(user) if user else {}
    facts = compute_facts_status(user_profile=user_profile, user_settings=settings)

    gates = compute_gates_status(user_status=user_status, facts=facts)

    # --- discovery gates (source of truth) ---
    discovery_status = (settings.get("discovery_status") or "pending").strip().lower()
    discovery_complete = (discovery_status == "complete")

    # smalltalk eligibility vient de compute_gates_status (dataclass)
    smalltalk_intro_eligible = bool(gates.smalltalk_intro_eligible)

    # Forced discovery: si smalltalk terminé (plus éligible) ET discovery pas complete
    forced_discovery = (not smalltalk_intro_eligible) and (not discovery_complete)

    # Transition window = condition 2 (free + quota ok + facts complets)
    is_pro = bool(user_status.get("is_pro"))
    used = int(user_status.get("free_quota_used") or 0)
    limit = int(user_status.get("free_quota_limit") or 0)
    quota_ok = used < limit

    facts_complete = (int(facts.missing_count or 0) == 0)

    transition_window = (not is_pro) and quota_ok and facts_complete
    transition_reason = "free_quota_ok_facts_complete" if transition_window else None

    # 5) persisted user facts (DB) — non destructif
    facts_store: List[Dict[str, Any]] = []
    try:
        fact_rows = await conn.fetch(
            """
            select
              fact_key,
              category,
              scope,
              value_type,
              value,
              confidence,
              is_estimated,
              source_ref,
              notes,
              updated_at
            from public.user_facts
            where user_id = $1
            order by updated_at desc nulls last
            limit 200
            """,
            public_user_id,
        )
        facts_store = [dict(r) for r in fact_rows]
    except Exception:
        # Si la table n'existe pas encore / pas migrée / autre: on n'explose pas le chat
        facts_store = []

    # 6) docs scopes list (source of truth for orchestrator)
    docs_scopes: List[str] = []
    try:
        scope_rows = await conn.fetch(
            """
            select distinct doc_scope
            from public.lisa_service_docs
            where doc_scope is not null and doc_scope <> ''
            order by doc_scope asc
            """
        )
        docs_scopes = [str(r["doc_scope"]) for r in scope_rows if r.get("doc_scope")]
    except Exception:
        docs_scopes = []

    # --- Conversation thread state (derived from last 10 messages) ---
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

    # 7) Agents actifs + catalog (actions & intégrations requises)
    user_agents = []
    try:
        user_agents = await conn.fetch(
            """
            select agent_key, status, onboarding_status, revoked_at
            from public.lisa_user_agents
            where user_id = $1
              and status = 'active'
              and revoked_at is null
            """,
            public_user_id,
        )
    except Exception:
        user_agents = []

    active_agent_keys = [str(r["agent_key"]) for r in user_agents if r.get("agent_key")]

    # --- Onboarding / Pro mode (source de vérité: lisa_user_agents + lisa_agents_catalog) ---
    primary_agent_key = None
    onboarding_status = None  # "started" | "complete" | None

    for r in user_agents:
        ak = r.get("agent_key")
        if ak:
            primary_agent_key = str(ak)
            ob = r.get("onboarding_status")
            onboarding_status = (str(ob) if ob is not None else None)
            break

    # pro_mode = tout sauf personal_assistant (inclut Ultimate + modes pro)
    pro_mode = bool(primary_agent_key) and (primary_agent_key != "personal_assistant")

    # playbook full du mode concerné (si pro_mode)
    playbook_full = None
    if pro_mode and primary_agent_key:
        row = (agents_by_key.get(primary_agent_key) or {})
        pb = row.get("lisa_playbook")
        if isinstance(pb, str) and pb.strip():
            playbook_full = pb.strip()

    agents_catalog = []
    try:
        agents_catalog = await conn.fetch(
            """
            select
              agent_key,
              title,
              requires_subscription,
              requires_integrations,
              executable_actions,
              lisa_playbook
            from public.lisa_agents_catalog
            where agent_key = any($1::text[])
            """,
            active_agent_keys,
        )
    except Exception:
        agents_catalog = []

    agents_by_key = {str(r["agent_key"]): dict(r) for r in agents_catalog if r.get("agent_key")}

    # 8) Intégrations connectées du user
    connected_integrations = []
    try:
        integ_rows = await conn.fetch(
            """
            select integration_key, status, connected_at
            from public.lisa_user_integrations
            where user_id = $1
              and status = 'connected'
            """,
            public_user_id,
        )
        connected_integrations = [str(r["integration_key"]) for r in integ_rows if r.get("integration_key")]
    except Exception:
        connected_integrations = []

    # 9) Capabilities (déterministe)
    has_paid_agent = False
    can_action_request = False
    can_professional_request = False
    can_deep_work = True

    # actions autorisées (keys)
    allowed_action_keys = set()

    # intégrations requises (union)
    all_required_integrations = set()

    for k in active_agent_keys:
        row = agents_by_key.get(k) or {}
        if bool(row.get("requires_subscription")):
            has_paid_agent = True

        # executable_actions = liste de action_key autorisées pour cet agent
        ea = row.get("executable_actions") or []
        if isinstance(ea, list) and len(ea) > 0:
            can_action_request = True
            for a in ea:
                if isinstance(a, str) and a.strip():
                    allowed_action_keys.add(a.strip())

        # requires_integrations = intégrations globales requises par l’agent (si tu veux)
        ri = row.get("requires_integrations") or []
        if isinstance(ri, list):
            for x in ri:
                if isinstance(x, str) and x.strip():
                    all_required_integrations.add(x.strip())

    # 9bis) Résoudre les intégrations requises par ACTIONS via lisa_actions_catalog
    actions_catalog = []
    if allowed_action_keys:
        try:
            actions_catalog = await conn.fetch(
                """
                select action_key, required_integrations, status
                from public.lisa_actions_catalog
                where action_key = any($1::text[])
                """,
                list(allowed_action_keys),
            )
        except Exception:
            actions_catalog = []

    # map action_key -> required_integrations
    action_required_integrations = {}
    active_allowed_actions = set()

    for r in actions_catalog:
        key = str(r["action_key"])
        status = str(r.get("status") or "active")
        if status != "active":
            continue
        active_allowed_actions.add(key)

        req = r.get("required_integrations") or []
        if isinstance(req, list):
            action_required_integrations[key] = [str(x) for x in req if isinstance(x, str) and x.strip()]
            for x in action_required_integrations[key]:
                all_required_integrations.add(x)

    # IMPORTANT:
    # - active_allowed_actions = actions autorisées ET actives dans le catalogue
    # - allowed_action_keys peut contenir des clés pas encore en table => on les ignore dans active list
    action_state = {
        "active_agent_keys": active_agent_keys,
        "has_paid_agent": has_paid_agent,
        "can_action_request": can_action_request,

        # actions réellement exploitables (catalog active)
        "executable_actions": sorted(list(active_allowed_actions)),
        "action_required_integrations": action_required_integrations,

        "required_integrations": sorted(list(all_required_integrations)),
        "connected_integrations": connected_integrations,
    }

    # NOTE: onboarding_status viendra après (quand on l'ajoutera en DB)


    return {
        "user": (
            {
                **dict(user),
                "id": str(user["id"]) if user.get("id") else None,
            }
            if user else None
        ),
        "settings": settings,
        "messages": messages,
        "user_status": user_status,

        # ✅ Ajouts non destructifs
        "user_facts": {
            "required_keys": facts.required_keys,
            "known": facts.known,
            "missing_required": facts.missing,
            "missing_required_count": facts.missing_count,
        },
        "facts_store": {
            "count": len(facts_store),
            "items": facts_store,
            "keys": [f.get("fact_key") for f in facts_store[:50] if isinstance(f, dict)],
        },
        "history": {
            "messages": messages,  # alias explicite (orchestrator prompt parle de ctx.history.messages)
            "last_user_message": last_user_message,
            "last_assistant_message": last_assistant_message,
            "last_assistant_intent_final": last_assistant_intent,
            "last_assistant_mode": last_assistant_mode,
        },
        "gates": {
            # smalltalk gates existants
            "smalltalk_intro_eligible": gates.smalltalk_intro_eligible,
            "smalltalk_target_key": gates.smalltalk_target_key,
            "missing_required": facts.missing,

            # discovery gates (nouveaux)
            "discovery_status": discovery_status,
            "discovery_forced": bool(forced_discovery),

            # transition window (flag autonome)
            "transition_window": bool(transition_window),
            "transition_reason": transition_reason,
        },
        "capabilities": {
            "has_paid_agent": bool(action_state.get("has_paid_agent")),
            "can_action_request": bool(action_state.get("can_action_request")),
            "can_deep_work": bool(can_deep_work),
            "can_professional_request": bool(can_professional_request),
        },
        "onboarding": {
            "status": onboarding_status,   # "started" | "complete" | None
            "pro_mode": bool(pro_mode),
            "primary_agent_key": primary_agent_key,
            "playbook_full": playbook_full,  # str | None
        },
        "action_state": action_state,
        "docs": {
            "scopes_all": docs_scopes,
            "scopes_count": len(docs_scopes),
        },
    }