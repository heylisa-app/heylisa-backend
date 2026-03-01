# app/services/intent_routing/gates.py

from typing import Any, Dict

def apply_gates(*, ctx: Dict[str, Any]) -> Dict[str, Any]:
    ctx = ctx or {}
    user_status = (ctx.get("user_status") or {})

    quota_state = str(user_status.get("state") or "normal").strip().lower()

    soft_paywall_warning = (quota_state == "warn_last_free")

    return {
        "soft_paywall_warning": soft_paywall_warning,
    }