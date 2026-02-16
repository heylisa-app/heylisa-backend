# app/services/message_flags.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any
import re

# Match une ligne "flag=true" (avec espaces, casse, etc.)
_FLAG_LINE_RE = re.compile(
    r"""(?im)^\s*(aha_moment|onboarding_abort)\s*=\s*(true|false|1|0)\s*$"""
)

@dataclass
class MessageFlags:
    aha_moment: bool = False
    onboarding_abort: bool = False

    def to_metadata(self) -> Dict[str, Any]:
        return {
            "aha_moment": bool(self.aha_moment),
            "onboarding_abort": bool(self.onboarding_abort),
        }

def extract_and_clean_message_flags(text: str) -> tuple[str, MessageFlags]:
    """
    - Détecte les flags (lignes seules) : aha_moment=..., onboarding_abort=...
    - Les retire du texte
    - Retourne (clean_text, flags)
    """
    flags = MessageFlags()

    if not text:
        return "", flags

    lines = text.splitlines()
    kept: list[str] = []

    for ln in lines:
        m = _FLAG_LINE_RE.match(ln)
        if not m:
            kept.append(ln)
            continue

        key = (m.group(1) or "").strip().lower()
        val_raw = (m.group(2) or "").strip().lower()
        val = val_raw in ("true", "1")

        if key == "aha_moment":
            flags.aha_moment = flags.aha_moment or val
        elif key == "onboarding_abort":
            flags.onboarding_abort = flags.onboarding_abort or val

        # on ne garde pas cette ligne

    clean = "\n".join(kept).strip()
    return clean, flags