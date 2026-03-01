# app/prompts/user/loader.py

from __future__ import annotations

from typing import Dict, Optional, Literal

from app.prompts.user.v1.registry import (
    USER_BLOCKS_BY_STATE,
    USER_BLOCKS_BY_INTENT,
    USER_BLOCKS_MISC,
)


def _render_template(text: str, vars: Dict[str, str]) -> str:
    """
    Micro-templating ultra simple.
    Remplace {{key}} par vars[key] si présent, sinon laisse tel quel.
    """
    out = text or ""
    for k, v in (vars or {}).items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def load_user_prompt_block(
    *,
    # ✅ NEW
    kind: Literal["state", "intent", "misc"] = "intent",
    key: Optional[str] = None,
    vars: Optional[Dict[str, str]] = None,
    # ✅ COMPAT (ancien appel)
    intent: Optional[str] = None,
) -> str:
    """
    Charge un bloc de prompt.
    - Nouveau mode: kind + key
    - Compat: intent=... (traité comme kind="intent")
    """
    k = (key or intent or "").strip()
    if not k:
        return ""

    if kind == "state":
        block = USER_BLOCKS_BY_STATE.get(k)
    elif kind == "misc":
        block = USER_BLOCKS_MISC.get(k)
    else:
        # kind == "intent" (default)
        block = USER_BLOCKS_BY_INTENT.get(k)

    if not block:
        return ""

    return _render_template(block.content, vars or {})

def get_user_prompt_keys(kind: Literal["state", "intent", "misc"]) -> set[str]:
    if kind == "state":
        return set(USER_BLOCKS_BY_STATE.keys())
    if kind == "misc":
        return set(USER_BLOCKS_MISC.keys())
    return set(USER_BLOCKS_BY_INTENT.keys())