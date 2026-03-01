# app/services/onboarding_state.py

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from asyncpg import Connection


def compute_onboarding_target(ctx: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """
    Détermine si onboarding doit être actif et vers quelle cible.
    Fonction pure. Aucun accès DB.

    Retour:
    {
        "target": "personal" | "pro" | None,
        "reason": str | None
    }
    """

    onboarding_ctx = ctx.get("onboarding", {}) or {}
    gates = ctx.get("gates", {}) or {}

    row = onboarding_ctx.get("row") or {}

    has_paid_active = bool(onboarding_ctx.get("has_paid_active"))
    has_pro_mode_active = bool(onboarding_ctx.get("has_pro_mode_active"))
    discovery_status = (gates.get("discovery_status") or "").lower()

    level_max = (row.get("level_max") or "none").lower()

    # -------------------------------------------------
    # 1️⃣ Discovery pas complete → onboarding impossible
    # -------------------------------------------------
    if discovery_status != "complete":
        return {
            "target": None,
            "reason": "discovery_not_complete"
        }

    # -------------------------------------------------
    # 2️⃣ Pas d’abonnement actif → onboarding impossible
    # -------------------------------------------------
    if not has_paid_active:
        return {
            "target": None,
            "reason": "no_paid_active"
        }

    # -------------------------------------------------
    # 3️⃣ Si user a déjà level_max = pro → jamais d’onboarding
    # -------------------------------------------------
    if level_max == "pro":
        return {
            "target": None,
            "reason": "already_pro_onboarded"
        }

    # -------------------------------------------------
    # 4️⃣ Si pro mode actif → onboarding pro
    # -------------------------------------------------
    if has_pro_mode_active:
        return {
            "target": "pro",
            "reason": "pro_mode_active"
        }

    # -------------------------------------------------
    # 5️⃣ Sinon → onboarding personal
    # -------------------------------------------------
    return {
        "target": "personal",
        "reason": "personal_mode_only"
    }


async def apply_onboarding_state(
    conn: Connection,
    ctx: dict,
    public_user_id: str,
    is_user_message: bool,
) -> dict:
    """
    Applique la logique onboarding (start / increment / complete).
    Ne touche à rien si onboarding_target = None.
    """

    result = compute_onboarding_target(ctx)
    target = result.get("target")
    reason = result.get("reason")

    onboarding_ctx = ctx.get("onboarding", {}) or {}
    row = onboarding_ctx.get("row") or {}

    now = datetime.now(timezone.utc)

    level_max = (row.get("level_max") or "none").lower()
    status = row.get("status")
    counter = int(row.get("user_msgs_since_started") or 0)

    # -------------------------------------------------
    # 1️⃣ Aucun onboarding requis
    # -------------------------------------------------
    if target is None:
        return {
            "active": False,
            "target": None,
            "status": None,
            "reason": reason,
        }

    # -------------------------------------------------
    # 2️⃣ Première activation (row inexistante)
    # -------------------------------------------------
    if not row:
        await conn.execute(
            """
            insert into public.user_onboarding (
                user_id,
                level_max,
                target,
                status,
                user_msgs_since_started,
                started_at,
                updated_at
            )
            values ($1, 'none', $2, 'started', 0, $3, $3)
            """,
            public_user_id,
            target,
            now,
        )
        return {
            "active": True,
            "target": target,
            "status": "started",
            "reason": "onboarding_started_first_time",
        }

    # -------------------------------------------------
    # 3️⃣ Target change (personal -> pro)
    # -------------------------------------------------
    if target != row.get("target"):
        await conn.execute(
            """
            update public.user_onboarding
            set
                target = $2,
                status = 'started',
                user_msgs_since_started = 0,
                started_at = $3,
                updated_at = $3
            where user_id = $1
            """,
            public_user_id,
            target,
            now,
        )
        return {
            "active": True,
            "target": target,
            "status": "started",
            "reason": "onboarding_restarted_target_change",
        }

    # -------------------------------------------------
    # 4️⃣ Si onboarding déjà complete → rien à faire
    # -------------------------------------------------
    if status == "complete":
        return {
            "active": False,
            "target": None,
            "status": "complete",
            "reason": "already_complete",
        }

    # -------------------------------------------------
    # 5️⃣ Incrément compteur si message user
    # -------------------------------------------------
    if is_user_message:
        counter += 1
        await conn.execute(
            """
            update public.user_onboarding
            set
                user_msgs_since_started = $2,
                updated_at = $3
            where user_id = $1
            """,
            public_user_id,
            counter,
            now,
        )

    # -------------------------------------------------
    # 6️⃣ Conditions completion
    # -------------------------------------------------
    connected_tools_count = int(onboarding_ctx.get("connected_tools_count") or 0)

    complete = False
    completion_reason = None

    # --- Personal onboarding ---
    if target == "personal":
        if counter > 10:
            complete = True
            completion_reason = "personal_msg_threshold"

    # --- Pro onboarding ---
    if target == "pro":
        if connected_tools_count >= 1:
            complete = True
            completion_reason = "tool_connected"
        elif counter > 10:
            complete = True
            completion_reason = "pro_msg_threshold"

    # -------------------------------------------------
    # 7️⃣ Si complete → update level_max + reset compteur
    # -------------------------------------------------
    if complete:
        new_level = "pro" if target == "pro" else "personal"

        await conn.execute(
            """
            update public.user_onboarding
            set
                level_max = $2,
                status = 'complete',
                user_msgs_since_started = 0,
                completed_at = $3,
                updated_at = $3,
                last_completion_reason = $4
            where user_id = $1
            """,
            public_user_id,
            new_level,
            now,
            completion_reason,
        )

        return {
            "active": False,
            "target": None,
            "status": "complete",
            "reason": completion_reason,
        }

    # -------------------------------------------------
    # 8️⃣ Toujours en cours
    # -------------------------------------------------
    return {
        "active": True,
        "target": target,
        "status": "started",
        "reason": "in_progress",
        "counter": counter,
    }