from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional


State = Literal[
    "smalltalk_onboarding",
    "discovery_capabilities",
    "normal_run",
]


@dataclass
class StateDecision:
    state: State
    fastpath_allowed: bool = True
    transition_reason: Optional[str] = None


def _norm(value: Any, default: str = "") -> str:
    return str(value or default).strip().lower()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def resolve_state_v2(*, ctx: Dict[str, Any]) -> StateDecision:
    """
    Resolver V2 — logique métier médicale simplifiée.

    Règles:
    1. smalltalk_onboarding
       - si discovery_status == "to_do"
       - et user_messages_count < 8

    2. discovery_capabilities
       - si discovery_status == "pending"

    3. normal_run
       - si discovery_status == "complete"

    Fallback de sécurité:
       - tout le reste => normal_run
    """
    ctx = ctx or {}

    onboarding_state = (ctx.get("onboarding_state") or {})
    history = (ctx.get("history") or {})

    discovery_status = _norm(
        onboarding_state.get("discovery_status"),
        default="to_do",
    )

    user_messages_count = _safe_int(
        history.get("user_messages_count"),
        default=0,
    )

    if discovery_status == "to_do" and user_messages_count < 8:
        return StateDecision(
            state="smalltalk_onboarding",
            fastpath_allowed=True,
            transition_reason=(
                f"smalltalk_onboarding:"
                f"discovery_status={discovery_status},"
                f"user_messages_count={user_messages_count}"
            ),
        )

    if discovery_status == "pending":
        return StateDecision(
            state="discovery_capabilities",
            fastpath_allowed=True,
            transition_reason="discovery_status_pending",
        )

    if discovery_status == "complete":
        return StateDecision(
            state="normal_run",
            fastpath_allowed=False,
            transition_reason="discovery_status_complete",
        )

    return StateDecision(
        state="normal_run",
        fastpath_allowed=False,
        transition_reason=(
            f"fallback_normal_run:"
            f"discovery_status={discovery_status},"
            f"user_messages_count={user_messages_count}"
        ),
    )