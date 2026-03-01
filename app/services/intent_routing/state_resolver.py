# app/services/intent_routing/state_resolver.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

SMALLTALK_INTRO_MAX_USER_MSGS = 10
ONBOARDING_PRO_MAX_USER_MSGS = 20

State = Literal[
    "smalltalk_intro",
    "discovery",
    "discovery_pending",
    "onboarding",
    "ongoing_personal",
    "ongoing_pro",
]

EscaladeReason = Literal[
    "NEED_WEB_SEARCH",
    "NEED_CONTEXT_UPGRADE",
    "NEED_ACTION_EXECUTION",
    "COMPLEXITY_OVERFLOW",
]


@dataclass
class StateDecision:
    state: State

    # ✅ ce que chat.py attend
    fastpath_allowed: bool = False
    quota_blocked: bool = False
    soft_paywall_warning: bool = False

    transition_window: bool = False
    transition_reason: Optional[str] = None


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def resolve_state(*, ctx: Dict[str, Any]) -> StateDecision:
    """
    StateResolver déterministe — règles STRICTES (source de vérité).
    - discovery = fastpath (Lisa)
    - escalade gérée plus tard par Lisa (reasons) => pas ici
    """
    ctx = ctx or {}

    onboarding_runtime = ctx.get("onboarding_runtime") or {}
    onboarding_active = bool(onboarding_runtime.get("active"))
    onboarding_target = onboarding_runtime.get("target")

    gates = (ctx.get("gates") or {})
    settings = (ctx.get("settings") or {})
    user_status = (ctx.get("user_status") or {})
    onboarding = (ctx.get("onboarding") or {})
    action_state = (ctx.get("action_state") or {})

    # ---- Inputs "source de vérité" ----
    # ✅ source of truth = gates (dérivé), pas settings (persisté / potentiellement stale)
    intro_smalltalk_done = bool(gates.get("smalltalk_done_derived"))

    discovery_status = _norm(
        gates.get("discovery_status")
        or gates.get("discovery_status_derived")
        or settings.get("discovery_status")
        or "to_do"
    )  # to_do|pending|complete|aborted|null
    user_messages_count = int(gates.get("user_messages_count") or 0)


    # ---- Onboarding counters (DB source) ----
    onboarding_row = {}
    try:
        onboarding_row = (onboarding.get("row") or {}) if isinstance(onboarding, dict) else {}
    except Exception:
        onboarding_row = {}

    onboarding_user_msgs_since_started = 0
    try:
        onboarding_user_msgs_since_started = int(onboarding_row.get("user_msgs_since_started") or 0)
    except Exception:
        onboarding_user_msgs_since_started = 0

    has_pro_mode_active = False
    try:
        has_pro_mode_active = bool(onboarding.get("has_pro_mode_active") is True)
    except Exception:
        has_pro_mode_active = False
    
    # ----- fin -----

    keyfacts_remaining_raw = gates.get("keyfacts_remaining")
    try:
        keyfacts_remaining = int(keyfacts_remaining_raw) if keyfacts_remaining_raw is not None else 999
    except Exception:
        keyfacts_remaining = 999

    quota_state = _norm(user_status.get("state") or "normal")  # normal|warn_last_free|blocked
    quota_blocked = (quota_state == "blocked")
    soft_warn = (quota_state == "warn_last_free")

    is_pro = bool(user_status.get("is_pro"))

    active_agent_keys = action_state.get("active_agent_keys") or []
    if not isinstance(active_agent_keys, list):
        active_agent_keys = []
    active_agent_keys = [str(x).strip() for x in active_agent_keys if str(x).strip()]

    # EXACT match: {"personal_assistant"}
    is_personal_assistant_only = (set(active_agent_keys) == {"personal_assistant"})

    # ---- Transition window (STRICT) ----
    transition_window = (
        intro_smalltalk_done
        and (keyfacts_remaining <= 1)
        and (user_messages_count < 15)
        and (discovery_status == "to_do")
    )

    transition_reason = None
    if transition_window:
        transition_reason = (
            f"discovery_window:keyfacts_remaining={keyfacts_remaining},"
            f"user_messages_count={user_messages_count},"
            f"discovery_status={discovery_status}"
        )[:80]



    # ---- 1) Smalltalk intro => fastpath ----
    if not intro_smalltalk_done:
        # ✅ Cap safety : si on dépasse 10 msgs user sans valider intro_smalltalk_done,
        # on sort quand même vers ongoing_personal (évite blocage).
        if user_messages_count >= SMALLTALK_INTRO_MAX_USER_MSGS:
            return StateDecision(
                state="ongoing_personal",
                transition_window=False,
                transition_reason="smalltalk_intro_cap_reached",
            )

        return StateDecision(
            state="smalltalk_intro",
            fastpath_allowed=True,
            transition_window=False,
            transition_reason=None,
        )

    # ---- 2) Onboarding (nouvelle logique déterministe) ----
    if onboarding_active:
        # ✅ Cap safety : si on est en onboarding "pro" (pro mode actif),
        # on ne peut pas rester coincé : au-delà de 20 msgs user => ongoing_pro.
        if is_pro and (not is_personal_assistant_only) and has_pro_mode_active:
            if onboarding_user_msgs_since_started >= ONBOARDING_PRO_MAX_USER_MSGS:
                return StateDecision(
                    state="ongoing_pro",
                    transition_window=False,
                    transition_reason="onboarding_pro_cap_reached",
                )

        return StateDecision(
            state="onboarding",
            transition_window=False,
            transition_reason=None,
        )

    # ---- 3) DISCOVERY_PENDING (STRICT) ----
    # Si le user a accepté la mini-démo => on doit livrer l’AHA message (prompt state: discovery_pending)
    if is_pro and is_personal_assistant_only and discovery_status == "pending":
        return StateDecision(
            state="discovery_pending",
            fastpath_allowed=True,   # ✅ conseillé vu que docs_chunks est déjà chargé dans votre fastpath
            transition_window=False,
            transition_reason="discovery_pending",
        )

    # ---- 3) DISCOVERY (STRICT) ----
    # discovery si:
    # - is_pro == true
    # - active_agent_keys == {"personal_assistant"} exactement
    # - intro_smalltalk_done == true
    # - discovery_status != "complete"
    if is_pro and is_personal_assistant_only and discovery_status != "complete":
        return StateDecision(
            state="discovery",
            fastpath_allowed=True,
            transition_window=transition_window,
            transition_reason=transition_reason,
        )

    # ---- 4) Ongoing pro ----
    # Si user pro + au moins un agent actif autre que personal_assistant => ongoing_pro
    if is_pro and (not is_personal_assistant_only):
        return StateDecision(
            state="ongoing_pro",
            transition_window=transition_window,
            transition_reason=transition_reason,
        )

    # ---- 5) Ongoing personal ----
    return StateDecision(
        state="ongoing_personal",
        transition_window=transition_window,
        transition_reason=transition_reason,
    )