# app/services/context_loader.py
from __future__ import annotations
from typing import List, Dict, Any

from asyncpg import Connection
from app.services.smalltalk_state import compute_facts_status, compute_gates_status
from app.services.quota import get_quota_status


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
        select role, content, sent_at
        from public.conversation_messages
        where conversation_id = $1
        order by sent_at desc, id desc
        limit 10
        """,
        conversation_id,
    )

    # we fetched DESC => reverse to get chronological order
    rows = list(reversed(rows))

    messages = [
        {
            "role": "assistant" if r["role"] == "assistant" else "user",
            "content": r["content"],
            "sent_at": (r["sent_at"].isoformat() if r.get("sent_at") else None),
        }
        for r in rows
    ]

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
        "docs": {
            "scopes_all": docs_scopes,
            "scopes_count": len(docs_scopes),
        },
    }