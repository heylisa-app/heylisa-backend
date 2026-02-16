# app/services/smalltalk_state.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

REQUIRED_KEYS_ORDER = ["first_name", "use_tu_form", "main_city", "main_activity"]

@dataclass
class FactsStatus:
    required_keys: List[str]
    known: Dict[str, bool]
    missing: List[str]
    missing_count: int
    target_key: Optional[str]

@dataclass
class GatesStatus:
    smalltalk_intro_eligible: bool
    smalltalk_target_key: Optional[str]

def compute_facts_status(*, user_profile: Dict, user_settings: Dict) -> FactsStatus:
    # Mapping clair: où vit chaque fact
    # - first_name : user_profile (table users)
    # - use_tu_form : user_settings
    # - main_city : user_settings (ou profile selon ton modèle)
    # - main_activity : user_settings
    def has_str(x) -> bool:
        return isinstance(x, str) and x.strip() != ""

    first_name = (user_profile or {}).get("first_name")
    use_tu_form = (user_settings or {}).get("use_tu_form")  # bool|null
    main_city = (user_settings or {}).get("main_city") or (user_settings or {}).get("primary_city")
    main_activity = (user_settings or {}).get("main_activity")

    known = {
        "first_name": has_str(first_name),
        "use_tu_form": (use_tu_form is True) or (use_tu_form is False),
        "main_city": has_str(main_city),
        "main_activity": has_str(main_activity),
    }

    missing = [k for k in REQUIRED_KEYS_ORDER if not known.get(k, False)]
    target_key = missing[0] if missing else None

    return FactsStatus(
        required_keys=REQUIRED_KEYS_ORDER,
        known=known,
        missing=missing,
        missing_count=len(missing),
        target_key=target_key,
    )

def compute_gates_status(*, user_status: Dict, facts: FactsStatus) -> GatesStatus:
    # STRICTEMENT ta règle validée
    state = (user_status or {}).get("state")
    used = int((user_status or {}).get("free_quota_used") or 0)
    limit = int((user_status or {}).get("free_quota_limit") or 8)

    eligible = (state != "blocked") and (used < limit) and (facts.missing_count > 0)

    return GatesStatus(
        smalltalk_intro_eligible=eligible,
        smalltalk_target_key=facts.target_key,
    )