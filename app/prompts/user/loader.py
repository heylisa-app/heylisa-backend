from __future__ import annotations

from typing import Dict, Optional

from app.prompts.user.v1.registry import USER_BLOCKS_BY_INTENT


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
    intent: str,
    vars: Optional[Dict[str, str]] = None,
) -> str:
    block = USER_BLOCKS_BY_INTENT.get((intent or "").strip())
    if not block:
        return ""
    return _render_template(block.content, vars or {})