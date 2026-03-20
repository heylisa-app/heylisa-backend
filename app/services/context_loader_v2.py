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


def _normalize_specialties(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return []
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()]
        except Exception:
            pass
        return [raw]
    return []


def _safe_iso(dt: Any) -> Optional[str]:
    try:
        return dt.isoformat() if dt else None
    except Exception:
        return None


def _extract_preference_from_user_facts(user_facts: List[Dict[str, Any]]) -> Dict[str, Any]:
    use_tu_form = None
    preferred_name = None

    for fact in user_facts:
        fact_key = str(fact.get("fact_key") or "").strip().lower()
        value = fact.get("value")

        if fact_key == "use_tu_form" and use_tu_form is None:
            if isinstance(value, bool):
                use_tu_form = value
            elif isinstance(value, str):
                low = value.strip().lower()
                if low in {"true", "1", "yes", "oui"}:
                    use_tu_form = True
                elif low in {"false", "0", "no", "non"}:
                    use_tu_form = False

        if fact_key == "preferred_name" and not preferred_name:
            if value is not None:
                txt = str(value).strip()
                if txt:
                    preferred_name = txt

    return {
        "use_tu_form": use_tu_form,
        "preferred_name": preferred_name,
        "addressing_preference_known": (use_tu_form is True or use_tu_form is False),
    }


async def load_context_light(
    conn: Connection,
    public_user_id: str,
    conversation_id: str,
) -> dict:
    # ---------------------------------------------------
    # 1) Conversation
    # ---------------------------------------------------
    conversation_row = await conn.fetchrow(
        """
        select
          id,
          user_id,
          channel,
          context,
          status,
          started_at,
          last_message_at
        from public.conversations
        where id = $1::uuid
        limit 1
        """,
        conversation_id,
    )

    conversation = dict(conversation_row) if conversation_row else {
        "id": conversation_id,
        "user_id": public_user_id,
        "channel": None,
        "context": None,
        "status": None,
        "started_at": None,
        "last_message_at": None,
    }

    # ---------------------------------------------------
    # 2) User
    # ---------------------------------------------------
    user_row = await conn.fetchrow(
        """
        select
          id,
          auth_user_id,
          account_email,
          first_name,
          last_name,
          full_name,
          primary_company_id,
          onboarding_completed,
          created_at,
          updated_at
        from public.users
        where id = $1::uuid
        limit 1
        """,
        public_user_id,
    )

    user = dict(user_row) if user_row else {
        "id": public_user_id,
        "auth_user_id": None,
        "account_email": None,
        "first_name": None,
        "last_name": None,
        "full_name": None,
        "primary_company_id": None,
        "onboarding_completed": None,
        "created_at": None,
        "updated_at": None,
    }

    cabinet_account_id = user.get("primary_company_id")

    # ---------------------------------------------------
    # 3) Cabinet
    # ---------------------------------------------------
    cabinet = None
    if cabinet_account_id:
        cabinet_row = await conn.fetchrow(
            """
            select
              id,
              name,
              legal_name,
              slug,
              website,
              country_code,
              main_city,
              size,
              owner_user_id,
              status,
              trial_started_at,
              trial_ends_at,
              structure_type,
              specialties,
              created_at,
              updated_at
            from public.cabinet_accounts
            where id = $1::uuid
            limit 1
            """,
            cabinet_account_id,
        )

        if cabinet_row:
            cabinet = dict(cabinet_row)
            cabinet["specialties"] = _normalize_specialties(cabinet.get("specialties"))
            cabinet["id"] = str(cabinet["id"])
            cabinet["owner_user_id"] = str(cabinet["owner_user_id"]) if cabinet.get("owner_user_id") else None
            cabinet["trial_started_at"] = _safe_iso(cabinet.get("trial_started_at"))
            cabinet["trial_ends_at"] = _safe_iso(cabinet.get("trial_ends_at"))
            cabinet["created_at"] = _safe_iso(cabinet.get("created_at"))
            cabinet["updated_at"] = _safe_iso(cabinet.get("updated_at"))

    if cabinet is None:
        cabinet = {
            "id": str(cabinet_account_id) if cabinet_account_id else None,
            "name": None,
            "legal_name": None,
            "slug": None,
            "website": None,
            "country_code": None,
            "main_city": None,
            "size": None,
            "owner_user_id": None,
            "status": None,
            "trial_started_at": None,
            "trial_ends_at": None,
            "structure_type": None,
            "specialties": [],
            "created_at": None,
            "updated_at": None,
        }

    # ---------------------------------------------------
    # 4) Cabinet member courant
    # ---------------------------------------------------
    member = None
    if cabinet.get("id"):
        member_row = await conn.fetchrow(
            """
            select
              id,
              cabinet_account_id,
              user_id,
              email,
              full_name,
              role,
              status,
              job_role,
              invited_by_user_id,
              created_at,
              updated_at
            from public.cabinet_members
            where cabinet_account_id = $1::uuid
              and user_id = $2::uuid
            limit 1
            """,
            str(cabinet["id"]),
            str(public_user_id),
        )

        if member_row:
            member = dict(member_row)
            member["id"] = str(member["id"])
            member["cabinet_account_id"] = str(member["cabinet_account_id"]) if member.get("cabinet_account_id") else None
            member["user_id"] = str(member["user_id"]) if member.get("user_id") else None
            member["invited_by_user_id"] = str(member["invited_by_user_id"]) if member.get("invited_by_user_id") else None
            member["created_at"] = _safe_iso(member.get("created_at"))
            member["updated_at"] = _safe_iso(member.get("updated_at"))

    if member is None:
        member = {
            "id": None,
            "cabinet_account_id": cabinet.get("id"),
            "user_id": str(public_user_id),
            "email": user.get("account_email"),
            "full_name": user.get("full_name"),
            "role": None,
            "status": None,
            "job_role": None,
            "invited_by_user_id": None,
            "created_at": None,
            "updated_at": None,
        }

    onboarding_row = await conn.fetchrow(
        """
        select
          discovery_status,
          discovery_completed_at,
          intro_smalltalk_turns
        from public.user_onboarding_state
        where user_id = $1::uuid
        limit 1
        """,
        public_user_id,
    )

    onboarding_state = {
        "discovery_status": "to_do",
        "discovery_completed_at": None,
        "intro_smalltalk_turns": 0,
    }

    if onboarding_row:
        onboarding_state = {
            "discovery_status": str(onboarding_row["discovery_status"] or "to_do").strip().lower(),
            "discovery_completed_at": (
                onboarding_row["discovery_completed_at"].isoformat()
                if onboarding_row["discovery_completed_at"]
                else None
            ),
            "intro_smalltalk_turns": int(onboarding_row["intro_smalltalk_turns"] or 0),
        }

    # ---------------------------------------------------
    # 5) 30 derniers messages
    # ---------------------------------------------------
    message_rows = await conn.fetch(
        """
        select
          id,
          role,
          sender_type,
          content,
          sent_at,
          metadata,
          dedupe_key
        from public.conversation_messages
        where conversation_id = $1::uuid
        order by sent_at desc, id desc
        limit 30
        """,
        conversation_id,
    )

    message_rows = list(reversed(message_rows))

    messages: List[Dict[str, Any]] = []
    intro_sent = False

    for row in message_rows:
        r = dict(row)
        meta = _meta_to_dict(r.get("metadata"))
        dedupe_key = str(r.get("dedupe_key") or "")

        if dedupe_key.startswith("sys:intro:"):
            intro_sent = True

        messages.append(
            {
                "id": str(r.get("id")) if r.get("id") else None,
                "role": "assistant" if r.get("role") == "assistant" else "user",
                "sender_type": r.get("sender_type"),
                "content": r.get("content"),
                "sent_at": _safe_iso(r.get("sent_at")),
                "metadata": meta,
            }
        )

    # ---------------------------------------------------
    # 6) History helpers
    # ---------------------------------------------------
    last_user_message = None
    last_assistant_message = None

    for m in reversed(messages):
        if m.get("role") == "user" and last_user_message is None:
            last_user_message = m.get("content")
        if m.get("role") == "assistant" and last_assistant_message is None:
            last_assistant_message = m.get("content")
        if last_user_message is not None and last_assistant_message is not None:
            break

    # ---------------------------------------------------
    # 7) User facts
    # ---------------------------------------------------
    user_facts: List[Dict[str, Any]] = []
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
            where user_id = $1::uuid
            order by updated_at desc nulls last
            limit 200
            """,
            public_user_id,
        )
        user_facts = [dict(r) for r in fact_rows]
    except Exception:
        user_facts = []

    # ---------------------------------------------------
    # 8) Cabinet facts (best effort)
    # ---------------------------------------------------
    cabinet_facts: List[Dict[str, Any]] = []
    if cabinet.get("id"):
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
                from public.cabinet_facts
                where cabinet_account_id = $1::uuid
                order by updated_at desc nulls last
                limit 200
                """,
                cabinet["id"],
            )
            cabinet_facts = [dict(r) for r in fact_rows]
        except Exception:
            cabinet_facts = []

    # ---------------------------------------------------
    # 9) Preferences dérivées
    # ---------------------------------------------------
    prefs = _extract_preference_from_user_facts(user_facts)

    # ---------------------------------------------------
    # 10) Docs scopes (source de vérité = lisa_service_docs)
    # ---------------------------------------------------
    docs_scopes: List[str] = []
    try:
        doc_scope_rows = await conn.fetch(
            """
            select distinct doc_scope
            from public.lisa_service_docs
            where doc_scope is not null
              and btrim(doc_scope) <> ''
            order by doc_scope asc
            """
        )
        docs_scopes = [
            str(r["doc_scope"]).strip()
            for r in doc_scope_rows
            if r.get("doc_scope") and str(r["doc_scope"]).strip()
        ]
    except Exception:
        docs_scopes = []

    # ---------------------------------------------------
    # 10bis) Payload core context V2
    # ---------------------------------------------------
    return {
        "conversation": {
            "id": str(conversation.get("id")) if conversation.get("id") else str(conversation_id),
            "channel": conversation.get("channel"),
            "context": conversation.get("context"),
            "status": conversation.get("status"),
            "started_at": _safe_iso(conversation.get("started_at")),
            "last_message_at": _safe_iso(conversation.get("last_message_at")),
        },
        "user": {
            "id": str(user.get("id")) if user.get("id") else str(public_user_id),
            "auth_user_id": str(user.get("auth_user_id")) if user.get("auth_user_id") else None,
            "account_email": user.get("account_email"),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "full_name": user.get("full_name"),
            "onboarding_completed": user.get("onboarding_completed"),
            "primary_company_id": str(user.get("primary_company_id")) if user.get("primary_company_id") else None,
        },
        "member": member,
        "cabinet": cabinet,
        "onboarding_state": onboarding_state,
        "preferences": {
            "use_tu_form": prefs["use_tu_form"],
            "preferred_name": prefs["preferred_name"],
            "addressing_preference_known": prefs["addressing_preference_known"],
        },
        "facts": {
            "user_facts": user_facts,
            "cabinet_facts": cabinet_facts,
        },
        "docs": {
            "scopes_all": docs_scopes,
            "scopes_count": len(docs_scopes),
        },
        "history": {
            "messages": messages,
            "last_user_message": last_user_message,
            "last_assistant_message": last_assistant_message,
            "user_messages_count": sum(1 for m in messages if m.get("role") == "user"),
            "assistant_messages_count": sum(1 for m in messages if m.get("role") == "assistant"),
        },
        "runtime": {
            "intro_sent": intro_sent,
        },
    }


async def _load_billing_block(
    conn: Connection,
    public_user_id: str,
) -> Dict[str, Any]:
    row = await conn.fetchrow(
        """
        select
          public_user_id,
          billing_status,
          billing_substatus,
          trial_started_at,
          trial_ends_at,
          grace_ends_at,
          stripe_customer_id,
          stripe_invoice_id,
          stripe_hosted_invoice_url,
          stripe_portal_url,
          trial_feedback_context_active,
          trial_feedback_context_closed,
          created_at,
          updated_at
        from public.user_billing_status
        where public_user_id = $1::uuid
        limit 1
        """,
        public_user_id,
    )

    if not row:
        return {
            "public_user_id": str(public_user_id),
            "billing_status": None,
            "billing_substatus": None,
            "trial_started_at": None,
            "trial_ends_at": None,
            "grace_ends_at": None,
            "stripe_customer_id": None,
            "stripe_invoice_id": None,
            "stripe_hosted_invoice_url": None,
            "stripe_portal_url": None,
            "trial_feedback_context_active": False,
            "trial_feedback_context_closed": False,
            "created_at": None,
            "updated_at": None,
        }

    r = dict(row)

    return {
        "public_user_id": str(r.get("public_user_id")) if r.get("public_user_id") else str(public_user_id),
        "billing_status": r.get("billing_status"),
        "billing_substatus": r.get("billing_substatus"),
        "trial_started_at": _safe_iso(r.get("trial_started_at")),
        "trial_ends_at": _safe_iso(r.get("trial_ends_at")),
        "grace_ends_at": _safe_iso(r.get("grace_ends_at")),
        "stripe_customer_id": r.get("stripe_customer_id"),
        "stripe_invoice_id": r.get("stripe_invoice_id"),
        "stripe_hosted_invoice_url": r.get("stripe_hosted_invoice_url"),
        "stripe_portal_url": r.get("stripe_portal_url"),
        "trial_feedback_context_active": bool(r.get("trial_feedback_context_active") is True),
        "trial_feedback_context_closed": bool(r.get("trial_feedback_context_closed") is True),
        "created_at": _safe_iso(r.get("created_at")),
        "updated_at": _safe_iso(r.get("updated_at")),
    }


async def load_context_with_billing(
    conn: Connection,
    public_user_id: str,
    conversation_id: str,
) -> dict:
    ctx = await load_context_light(
        conn=conn,
        public_user_id=public_user_id,
        conversation_id=conversation_id,
    )

    ctx["billing"] = await _load_billing_block(
        conn=conn,
        public_user_id=public_user_id,
    )

    return ctx