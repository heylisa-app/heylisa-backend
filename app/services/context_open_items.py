#app/services/context_open_items.py

from __future__ import annotations

from typing import Any, Dict, List, Optional
from app.core.chat_logger import chat_logger
from asyncpg import Connection
from datetime import datetime, time
from zoneinfo import ZoneInfo
import json


def _build_local_context(*, is_first_day_message: bool) -> dict:
    tz = ZoneInfo("Europe/Paris")
    now = datetime.now(tz)

    hour = now.hour

    if 5 <= hour < 12:
        day_period = "morning"
    elif 12 <= hour < 18:
        day_period = "afternoon"
    elif 18 <= hour < 22:
        day_period = "evening"
    else:
        day_period = "night"

    return {
        "timezone": "Europe/Paris",
        "now_iso": now.isoformat(),
        "date_label": now.strftime("%A %d/%m/%Y"),
        "hour": hour,
        "day_period": day_period,
        "is_weekend": now.weekday() >= 5,
        "is_first_day_message": is_first_day_message,
    }


async def _count_open_items_lisa_messages_today(
    conn: Connection,
    *,
    public_user_id: str,
    cabinet_id: str,
) -> int:
    return int(
        await conn.fetchval(
            """
            select count(*)
            from public.open_items_chat_messages m
            join public.open_items_chat_sessions s
              on s.id = m.session_id
            where s.public_user_id = $1::uuid
              and s.cabinet_id = $2::uuid
              and m.sender_type = 'lisa'
              and m.sent_at >= date_trunc('day', now() at time zone 'Europe/Paris') at time zone 'Europe/Paris'
            """,
            public_user_id,
            cabinet_id,
        )
        or 0
    )


async def _load_cabinet_integrations(
    conn: Connection,
    *,
    cabinet_id: str,
) -> list[dict]:
    rows = await conn.fetch(
        """
        select integration_key, status, description, metadata
        from public.lisa_user_integrations
        where cabinet_account_id = $1::uuid
          and status in ('active', 'connected')
        order by integration_key asc
        """,
        cabinet_id,
    )

    return [
        {
            "integration_key": str(row["integration_key"]),
            "status": str(row["status"]),
            "description": row["description"],
            "metadata": row["metadata"] or {},
        }
        for row in rows
    ]


async def _load_cabinet_human_team_context(
    conn: Connection,
    *,
    cabinet_id: str,
) -> dict:
    rows = await conn.fetch(
        """
        select role, job_role
        from public.cabinet_members
        where cabinet_account_id = $1::uuid
          and status = 'active'
        """,
        cabinet_id,
    )

    has_secretary = False
    has_doctor = False

    for row in rows:
        role = str(row["role"] or "").lower()
        job_role = str(row["job_role"] or "").lower()
        combined = f"{role} {job_role}"

        if "secret" in combined or "secr" in combined:
            has_secretary = True

        if "doctor" in combined or "medecin" in combined or "médecin" in combined:
            has_doctor = True

    return {
        "has_human_secretary": has_secretary,
        "has_doctor": has_doctor,
        "active_members_count": len(rows),
    }


def _clean_info_request(row: Dict[str, Any]) -> Dict[str, Any]:
    raw_metadata = row.get("metadata") or {}

    if isinstance(raw_metadata, str):
        try:
            metadata = json.loads(raw_metadata)
        except Exception:
            metadata = {}
    elif isinstance(raw_metadata, dict):
        metadata = raw_metadata
    else:
        metadata = {}

    return {
        "id": str(row["id"]),
        "queue_id": str(row["queue_id"]) if row.get("queue_id") else None,
        "interaction_id": str(row["interaction_id"]) if row.get("interaction_id") else None,
        "title": row.get("title"),
        "reason": row.get("reason"),
        "priority": row.get("priority"),
        "request_kind": row.get("request_kind"),
        "target_role": row.get("target_role"),
        "missing_items": row.get("missing_items") or [],
        "tasks": row.get("tasks") or [],
        "metadata": metadata,
        "contact_id": metadata.get("selected_contact_id"),
        "patient_name": metadata.get("patient_name"),
        "message_subject": metadata.get("message_subject"),
    }


def _clean_mail_queue(row: Dict[str, Any]) -> Dict[str, Any]:
    payload = row.get("payload") or {}

    return {
        "id": str(row["id"]),
        "interaction_id": str(row.get("interaction_id")) if row.get("interaction_id") else None,
        "queue_type": row.get("queue_type"),
        "priority": row.get("priority"),
        "wait_reason": row.get("wait_reason"),
        "draft_subject": row.get("draft_subject"),
        "draft_body_preview": (row.get("draft_body_text") or "")[:300],
        "payload_summary": payload if isinstance(payload, dict) else {},
    }


async def _get_cabinet_row_for_user(conn: Connection, public_user_id: str):
    return await conn.fetchrow(
        """
        select ca.id, ca.name
        from public.cabinet_members cm
        join public.cabinet_accounts ca
          on ca.id = cm.cabinet_account_id
        where cm.user_id = $1::uuid
          and cm.status = 'active'
        order by cm.created_at asc
        limit 1
        """,
        public_user_id,
    )


async def _load_cabinet_settings_context(
    conn: Connection,
    *,
    cabinet_id: str,
) -> dict:
    row = await conn.fetchrow(
        """
        select
          has_human_secretary,
          business_timezone,
          business_days,
          business_hours_start,
          business_hours_end,
          out_of_hours_send_next_opening
        from public.cabinet_settings
        where cabinet_account_id = $1::uuid
        limit 1
        """,
        cabinet_id,
    )

    if not row:
        return {
            "has_human_secretary": False,
            "business_timezone": "Europe/Paris",
            "business_days": [1, 2, 3, 4, 5],
            "business_hours_start": "09:00:00",
            "business_hours_end": "18:00:00",
            "is_business_open_now": False,
            "out_of_hours_send_next_opening": True,
        }

    tz = ZoneInfo(str(row["business_timezone"] or "Europe/Paris"))
    now = datetime.now(tz)
    current_day = now.isoweekday()
    current_time = now.time()

    business_days = list(row["business_days"] or [])
    start_time = row["business_hours_start"]
    end_time = row["business_hours_end"]

    is_business_open_now = (
        current_day in business_days
        and start_time <= current_time <= end_time
    )

    return {
        "has_human_secretary": bool(row["has_human_secretary"]),
        "business_timezone": str(row["business_timezone"] or "Europe/Paris"),
        "business_days": business_days,
        "business_hours_start": str(start_time),
        "business_hours_end": str(end_time),
        "is_business_open_now": is_business_open_now,
        "out_of_hours_send_next_opening": bool(row["out_of_hours_send_next_opening"]),
    }


async def load_open_items_context(
    conn: Connection,
    *,
    public_user_id: str,
    priority_info_request_id: Optional[str] = None,
) -> Dict[str, Any]:
    # =========================
    # USER
    # =========================
    user_row = await conn.fetchrow(
        """
        select id, first_name, last_name
        from public.users
        where id = $1::uuid
        limit 1
        """,
        public_user_id,
    )

    if not user_row:
        raise ValueError("USER_NOT_FOUND")

    preferences_row = None
    try:
        preferences_row = await conn.fetchrow(
            """
            select use_tu_form
            from public.user_settings
            where user_id = $1::uuid
            limit 1
            """,
            public_user_id,
        )
    except Exception as e:
        chat_logger.info(
            "open_items_context.preferences_unavailable",
            public_user_id=str(public_user_id),
            error=str(e)[:180],
        )
        preferences_row = None

    # =========================
    # CABINET
    # =========================
    cabinet_row = await _get_cabinet_row_for_user(conn, public_user_id)

    if not cabinet_row:
        raise ValueError("CABINET_NOT_FOUND")

    cabinet_id = str(cabinet_row["id"])


    lisa_messages_today = await _count_open_items_lisa_messages_today(
        conn,
        public_user_id=public_user_id,
        cabinet_id=cabinet_id,
    )

    is_first_day_message = lisa_messages_today == 0

    use_tu_form = (
        preferences_row.get("use_tu_form")
        if preferences_row and preferences_row.get("use_tu_form") is not None
        else False
    )

    first_name = (user_row.get("first_name") or "").strip()
    last_name = (user_row.get("last_name") or "").strip()

    member_row = await conn.fetchrow(
        """
        select role, job_role
        from public.cabinet_members
        where user_id = $1::uuid
        and cabinet_account_id = $2::uuid
        and status = 'active'
        limit 1
        """,
        public_user_id,
        cabinet_id,
    )

    job_role = (member_row.get("job_role") if member_row else None) or ""
    role = (member_row.get("role") if member_row else None) or ""

    is_doctor = (
        "doctor" in job_role.lower()
        or "medecin" in job_role.lower()
        or "médecin" in job_role.lower()
        or "doctor" in role.lower()
        or "medecin" in role.lower()
        or "médecin" in role.lower()
    )

    if use_tu_form:
        address_label = first_name or "vous"
        address_mode = "informal_firstname"
    else:
        if is_doctor:
            address_label = f"Docteur {last_name}".strip() if last_name else "Docteur"
            address_mode = "formal_doctor"
        else:
            address_label = first_name or "vous"
            address_mode = "formal_firstname"

    integrations = await _load_cabinet_integrations(
        conn,
        cabinet_id=cabinet_id,
    )

    human_team = await _load_cabinet_human_team_context(
        conn,
        cabinet_id=cabinet_id,
    )

    cabinet_settings = await _load_cabinet_settings_context(
        conn,
        cabinet_id=cabinet_id,
    )

    # =========================
    # OPEN INFO REQUESTS
    # =========================
    info_rows = await conn.fetch(
        """
        select *
        from public.cabinet_info_requests
        where cabinet_id = $1::uuid
          and status = 'open'
        order by
          case priority
            when 'critical' then 4
            when 'high' then 3
            when 'normal' then 2
            when 'low' then 1
            else 0
          end desc,
          asked_at desc
        limit 20
        """,
        cabinet_id,
    )

    info_requests = [_clean_info_request(dict(r)) for r in info_rows]

    requested_info_request = None

    if priority_info_request_id:
        requested_row = await conn.fetchrow(
            """
            select *
            from public.cabinet_info_requests
            where id = $1::uuid
            and cabinet_id = $2::uuid
            and status = 'open'
            limit 1
            """,
            priority_info_request_id,
            cabinet_id,
        )

        if requested_row:
            requested_info_request = _clean_info_request(dict(requested_row))

            already_in_list = any(
                str(item.get("id")) == str(requested_info_request.get("id"))
                for item in info_requests
            )

            if not already_in_list:
                info_requests = [requested_info_request] + info_requests

    contact_ids = [
        item.get("contact_id")
        for item in info_requests
        if item.get("contact_id")
    ]

    contacts_by_id = {}

    if contact_ids:
        contact_rows = await conn.fetch(
            """
            select id, full_name, first_name, last_name, email, phone
            from public.patient_contacts
            where id::text = any($1::text[])
            """,
            [str(contact_id) for contact_id in contact_ids],
        )

        contacts_by_id = {
            str(row["id"]): dict(row)
            for row in contact_rows
        }

    for item in info_requests:
        contact_id = item.get("contact_id")
        contact = contacts_by_id.get(str(contact_id)) if contact_id else None

        if contact:
            item["contact_email"] = contact.get("email")
            item["contact_phone"] = contact.get("phone")
            item["patient_name"] = (
                contact.get("full_name")
                or " ".join(
                    part
                    for part in [
                        contact.get("first_name"),
                        contact.get("last_name"),
                    ]
                    if part
                ).strip()
                or item.get("patient_name")
            )
        else:
            item["contact_email"] = None
            item["contact_phone"] = None



    # =========================
    # SEEK_INFOS MAIL QUEUE ONLY
    # =========================
    mail_rows = await conn.fetch(
        """
        select *
        from public.cabinet_mail_queue
        where cabinet_id = $1::uuid
          and queue_type = 'seek_infos'
          and status <> 'done'
        order by
          case priority
            when 'critical' then 4
            when 'high' then 3
            when 'normal' then 2
            when 'low' then 1
            else 0
          end desc,
          created_at desc
        limit 20
        """,
        cabinet_id,
    )

    mail_queue = [_clean_mail_queue(dict(r)) for r in mail_rows]

    # =========================
    # PRIORITY ITEM
    # =========================
    priority_item = None

    if requested_info_request:
        priority_item = requested_info_request
    elif priority_info_request_id:
        raise ValueError("REQUESTED_INFO_REQUEST_NOT_FOUND")
    elif info_requests:
        priority_item = info_requests[0]

    chat_logger.info(
        "open_items_context.priority_resolved",
        requested_priority_info_request_id=priority_info_request_id,
        resolved_priority_item_id=(priority_item or {}).get("id"),
        resolved_priority_item_title=(priority_item or {}).get("title"),
    )

    priority_queue_item = None
    if priority_item and priority_item.get("queue_id"):
        priority_queue_id = priority_item["queue_id"]
        for queue_item in mail_queue:
            if queue_item["id"] == priority_queue_id:
                priority_queue_item = queue_item
                break

    return {
        "interlocutor": {
            "id": str(user_row["id"]),
            "role": role,
            "job_role": job_role,
            "first_name": first_name,
            "last_name": last_name,
            "display_name": " ".join([x for x in [first_name, last_name] if x]).strip(),
            "use_tu_form": use_tu_form,
            "address_label": address_label,
            "address_mode": address_mode,
        },
        "user": {
            "id": str(user_row["id"]),
            "first_name": user_row.get("first_name"),
            "last_name": user_row.get("last_name"),
        },
        "preferences": {
            "preferred_name": None,
            "use_tu_form": preferences_row.get("use_tu_form") if preferences_row else None,
        },
        "cabinet": {
            "id": cabinet_id,
            "name": cabinet_row.get("name"),
        },
        "open_items": {
            "priority_item": priority_item,
            "priority_queue_item": priority_queue_item,
            "info_requests": info_requests,
            "mail_queue": mail_queue,
            "other_items_summary": sorted(
                [
                    {
                        "id": item.get("id"),
                        "title": item.get("title"),
                        "priority": item.get("priority"),
                        "reason": item.get("reason"),
                    }
                    for item in info_requests
                    if not priority_item or item.get("id") != priority_item.get("id")
                ],
                key=lambda item: {
                    "critical": 4,
                    "high": 3,
                    "normal": 2,
                    "low": 1,
                }.get(str(item.get("priority") or "normal").lower(), 0),
                reverse=True,
            )[:5],
        },
        "local_context": _build_local_context(
            is_first_day_message=is_first_day_message,
        ),
        "integrations": integrations,
        "human_team": human_team,
        "cabinet_settings": cabinet_settings,
    }