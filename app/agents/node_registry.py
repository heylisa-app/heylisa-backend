# app/agents/node_registry.py
from __future__ import annotations

from typing import Final, Tuple

# ✅ Source de vérité unique
NODE_TYPE_WHITELIST: Final[Tuple[str, ...]] = (
    "tool.db_load_context",
    "tool.quota_check",
    "tool.web_search",
    "agent.response_writer",
    "tool.docs_chunks",
    "tool.onboarding_update",
)

# ✅ Convention IDs (pareil: source unique)
DEFAULT_NODE_IDS: Final[Tuple[str, ...]] = ("A", "B", "C", "D", "S")


def render_nodes_whitelist_block() -> str:
    lines = "\n".join([f"- {t}" for t in NODE_TYPE_WHITELIST])
    return (
        "NODES DISPONIBLES (WHITELIST STRICTE)\n"
        "Tu n’as le droit d’utiliser QUE ces node types (interdit d’en inventer d’autres) :\n"
        f"{lines}\n"
    )


def render_ids_rules_block() -> str:
    ids = ", ".join(DEFAULT_NODE_IDS)
    return (
        "RÈGLES SUR LES IDs\n"
        f"- Utilise {ids} (dans cet ordre) sauf si besoin particulier.\n"
        "- Ne réutilise jamais le même id deux fois.\n"
    )