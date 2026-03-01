# app/tools/user_onboarding.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
from asyncpg import Connection
from datetime import datetime, timezone


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _clean_str(x: Any) -> str:
    s = (str(x or "")).strip()
    return s


def _is_non_empty(x: Any) -> bool:
    if x is None:
        return False
    if isinstance(x, str):
        return bool(x.strip())
    if isinstance(x, (list, dict)):
        return len(x) > 0
    return True


async def sync_user_onboarding(conn: Connection, *, user_id: str) -> Dict[str, Any]:
    """
    Source of truth: public.user_onboarding (+ lisa_user_agents, lisa_user_integrations).
    - Create row if missing.
    - Set status='started' when pro mode is active and status is null.
    - Set status='complete' when:
        all_required_keys_present == true
        AND (connected_integrations non vide OR first_action_done == true)
    - Never downgrade (complete stays complete).
    - Update metadata jsonb with computed fields.
    """

    # 1) Is pro mode active? (any active agent != personal_assistant)
    pro_mode_active = bool(
        await conn.fetchval(
            """
            select exists(
              select 1
              from public.lisa_user_agents
              where user_id = $1
                and status = 'active'
                and revoked_at is null
                and agent_key <> 'personal_assistant'
            )
            """,
            user_id,
        )
    )

    # 2) Connected integrations NOW
    connected_integrations: List[str] = []
    try:
        rows = await conn.fetch(
            """
            select integration_key
            from public.lisa_user_integrations
            where user_id = $1
              and status = 'connected'
            """,
            user_id,
        )
        connected_integrations = [str(r["integration_key"]) for r in rows if r.get("integration_key")]
    except Exception:
        connected_integrations = []

    connected_integrations_count = len(connected_integrations)

    # 3) Load onboarding row (create if missing)
    row = await conn.fetchrow(
        """
        select
          user_id,
          level_max,
          target,
          status,
          user_msgs_since_started,
          started_at,
          completed_at,
          metadata
        from public.user_onboarding
        where user_id = $1
        """,
        user_id,
    )

    if not row:
        await conn.execute(
            """
            insert into public.user_onboarding (user_id, status, metadata)
            values ($1, null, '{}'::jsonb)
            on conflict (user_id) do nothing
            """,
            user_id,
        )
        row = await conn.fetchrow(
            """
            select
              user_id,
              level_max,
              target,
              status,
              user_msgs_since_started,
              started_at,
              completed_at,
              metadata
            from public.user_onboarding
            where user_id = $1
            """,
            user_id,
        )

    # Safety
    status = _clean_str(row["status"]) if row and row.get("status") is not None else ""
    status = status.lower() if status else None

    level_max = row.get("level_max")
    target = row.get("target")

    metadata = row.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {}

    # 4) Required keys logic (simple now, extensible later)
    # Default required keys => based on the "key fields" of user_onboarding
    required_keys = metadata.get("required_keys")
    if not isinstance(required_keys, list) or not required_keys:
        required_keys = ["target", "level_max"]

    present_keys: List[str] = []
    value_map = {
        "target": target,
        "level_max": level_max,
    }
    for k in required_keys:
        if isinstance(k, str) and k in value_map and _is_non_empty(value_map[k]):
            present_keys.append(k)

    all_required_keys_present = len(present_keys) == len([k for k in required_keys if isinstance(k, str)])

    # 5) first_action_done (for now: stored flag in metadata, default false)
    first_action_done = bool(metadata.get("first_action_done") is True)

    # 6) Completion rule (your spec)
    should_complete = bool(all_required_keys_present) and (
        connected_integrations_count > 0 or first_action_done
    )

    # 7) Compute next status (never downgrade)
    next_status: Optional[str] = status

    if status == "complete":
        next_status = "complete"
    else:
        # Start when pro mode becomes active (and we weren't started yet)
        if (status is None or status == "") and pro_mode_active:
            next_status = "started"

        # Complete when rule is satisfied
        if should_complete:
            next_status = "complete"

    # 8) Prepare metadata patch (computed, deterministic)
    meta_patch: Dict[str, Any] = {
        "required_keys": required_keys,
        "present_keys": present_keys,
        "all_required_keys_present": bool(all_required_keys_present),
        "connected_integrations": connected_integrations,
        "connected_integrations_count": int(connected_integrations_count),
        "first_action_done": bool(first_action_done),
        "pro_mode_active": bool(pro_mode_active),
        "version": int(metadata.get("version") or 0) + 1,
        "last_update_source": "backend",
        "last_updated_at": _now().isoformat(),
    }

    # 9) Apply DB update if needed
    started_at = row.get("started_at")
    completed_at = row.get("completed_at")

    set_started_at = started_at
    set_completed_at = completed_at

    if next_status == "started" and not started_at:
        set_started_at = _now()
    if next_status == "complete" and not completed_at:
        set_completed_at = _now()

    should_inc = (next_status == "started")

    await conn.execute(
        """
        update public.user_onboarding
        set
          status = $2,
          started_at = $3,
          completed_at = $4,
          user_msgs_since_started = case
            when $6 then coalesce(user_msgs_since_started, 0) + 1
            else coalesce(user_msgs_since_started, 0)
          end,
          metadata = coalesce(metadata, '{}'::jsonb) || $5::jsonb
        where user_id = $1
        """,
        user_id,
        next_status,
        set_started_at,
        set_completed_at,
        meta_patch,
        should_inc,
    )

    return {
        "ok": True,
        "user_id": user_id,
        "status_prev": status,
        "status_next": next_status,
        "should_complete": bool(should_complete),
        "meta_patch": meta_patch,
    }

async def set_onboarding_fields(
    conn: Connection,
    *,
    user_id: str,
    target: Optional[str] = None,
    level_max: Optional[str] = None,
    metadata_patch: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Single write entrypoint for onboarding fields.
    - Updates target / level_max (only if provided and non-empty)
    - Merges optional metadata_patch into metadata
    - Calls sync_user_onboarding() after update
    """

    # 1) Normalize inputs
    tgt = _clean_str(target) if target is not None else ""
    lvl = _clean_str(level_max) if level_max is not None else ""

    patch = metadata_patch or {}
    if not isinstance(patch, dict):
        patch = {}

    # 2) Ensure row exists (so update always works)
    await conn.execute(
        """
        insert into public.user_onboarding (user_id, status, metadata)
        values ($1, null, '{}'::jsonb)
        on conflict (user_id) do nothing
        """,
        user_id,
    )

    # 3) Update fields (only when provided)
    await conn.execute(
        """
        update public.user_onboarding
        set
          target = case when $2 <> '' then $2 else target end,
          level_max = case when $3 <> '' then $3 else level_max end,
          metadata = coalesce(metadata, '{}'::jsonb) || $4::jsonb
        where user_id = $1
        """,
        user_id,
        tgt,
        lvl,
        patch,
    )

    # 4) Sync immediately (so status can flip started/complete)
    sync_res = await sync_user_onboarding(conn, user_id=user_id)

    return {
        "ok": True,
        "user_id": user_id,
        "updated": {
            "target": tgt if tgt else None,
            "level_max": lvl if lvl else None,
            "metadata_patch_keys": list(patch.keys())[:30],
        },
        "sync": sync_res,
    }