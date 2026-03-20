from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo
from asyncpg import Connection


class ChatIntroContextError(Exception):
    pass


def _safe_timezone(tz_name: str | None) -> str:
    if not tz_name:
        return "Europe/Paris"
    try:
        ZoneInfo(tz_name)
        return tz_name
    except Exception:
        return "Europe/Paris"


def _local_time_info(timezone_name: str) -> dict:
    tz = ZoneInfo(_safe_timezone(timezone_name))
    now = datetime.now(tz)

    return {
        "local_iso": now.isoformat(timespec="minutes"),
        "hour": now.hour,
        "minute": now.minute,
        "weekday_index": now.weekday(),
        "weekday_name_fr": [
            "lundi",
            "mardi",
            "mercredi",
            "jeudi",
            "vendredi",
            "samedi",
            "dimanche",
        ][now.weekday()],
        "is_weekend": now.weekday() >= 5,
    }


async def load_chat_intro_context(
    conn: Connection,
    *,
    public_user_id: str,
) -> dict:
    user_row = await conn.fetchrow(
        """
        select
          u.id,
          u.first_name,
          u.last_name,
          u.full_name,
          us.locale_main,
          us.timezone,
          us.use_tu_form,
          u.primary_company_id
        from public.users u
        left join public.user_settings us
          on us.user_id = u.id
        where u.id = $1::uuid
        """,
        public_user_id,
    )

    if not user_row:
        raise ChatIntroContextError("USER_NOT_FOUND")

    user = dict(user_row)

    cabinet_id = user.get("primary_company_id")
    if not cabinet_id:
        raise ChatIntroContextError("CABINET_NOT_FOUND")

    cabinet_row = await conn.fetchrow(
        """
        select
          id,
          name,
          status,
          structure_type,
          specialties
        from public.cabinet_accounts
        where id = $1::uuid
        """,
        cabinet_id,
    )

    if not cabinet_row:
        raise ChatIntroContextError("CABINET_NOT_FOUND")

    member_row = await conn.fetchrow(
        """
        select
          id,
          role,
          status,
          full_name,
          job_role,
          email
        from public.cabinet_members
        where cabinet_account_id = $1::uuid
          and user_id = $2::uuid
        limit 1
        """,
        cabinet_id,
        public_user_id,
    )

    if not member_row:
        raise ChatIntroContextError("CABINET_MEMBER_NOT_FOUND")

    locale_main = user.get("locale_main") or "fr-FR"
    timezone_name = _safe_timezone(user.get("timezone") or "Europe/Paris")

    return {
        "user": {
            "id": str(user.get("id")),
            "first_name": user.get("first_name"),
            "last_name": user.get("last_name"),
            "full_name": user.get("full_name"),
            "locale_main": locale_main,
            "timezone": timezone_name,
            "use_tu_form": user.get("use_tu_form"),
        },
        "member": {
            "role": member_row.get("role"),
            "status": member_row.get("status"),
            "full_name": member_row.get("full_name"),
            "job_role": member_row.get("job_role"),
            "email": member_row.get("email"),
        },
        "cabinet": {
            "id": str(cabinet_row.get("id")),
            "name": cabinet_row.get("name"),
            "status": cabinet_row.get("status"),
            "structure_type": cabinet_row.get("structure_type"),
            "specialties": cabinet_row.get("specialties") or [],
        },
        "time": _local_time_info(timezone_name),
    }