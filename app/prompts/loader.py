# app/prompts/loader.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple


# Base dir: app/prompts/
PROMPTS_DIR = Path(__file__).resolve().parent

# Cache simple en mémoire (process-level)
# key = (rel_path, mtime_ns) -> content
_CACHE: Dict[Tuple[str, int], str] = {}
# last chosen mtime per rel_path
_LAST_MTIME: Dict[str, int] = {}


class PromptLoadError(RuntimeError):
    pass


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        raise PromptLoadError(f"PROMPT_READ_ERROR: {path}: {e}") from e


def load_prompt(rel_path: str, *, allow_empty: bool = False) -> str:
    """
    Charge un prompt depuis app/prompts/<rel_path>.
    Cache en mémoire, invalide automatiquement si le fichier change (mtime).
    """
    rel_path = rel_path.strip().lstrip("/")

    path = (PROMPTS_DIR / rel_path).resolve()
    if not str(path).startswith(str(PROMPTS_DIR.resolve())):
        raise PromptLoadError(f"PROMPT_PATH_TRAVERSAL_BLOCKED: {rel_path}")

    if not path.exists() or not path.is_file():
        raise PromptLoadError(f"PROMPT_NOT_FOUND: {rel_path}")

    mtime = path.stat().st_mtime_ns
    cache_key = (rel_path, mtime)

    # cache hit si mtime identique
    if _LAST_MTIME.get(rel_path) == mtime and cache_key in _CACHE:
        return _CACHE[cache_key]

    content = _read_text_file(path).strip("\n")

    if (not content.strip()) and (not allow_empty):
        raise PromptLoadError(f"PROMPT_EMPTY_NOT_ALLOWED: {rel_path}")

    # purge cache précédent si le fichier a changé
    old_mtime = _LAST_MTIME.get(rel_path)
    if old_mtime is not None and old_mtime != mtime:
        old_key = (rel_path, old_mtime)
        _CACHE.pop(old_key, None)

    _CACHE[cache_key] = content
    _LAST_MTIME[rel_path] = mtime
    return content


def get_signature_version(default: str = "v1") -> str:
    """
    Version globale (env). Plus tard tu pourras override par user_settings.
    """
    v = (os.getenv("LISA_SIGNATURE_VERSION") or "").strip()
    return v if v else default


def load_lisa_system_prompts(version: Optional[str] = None) -> dict:
    """
    Retourne les blocs system prompts versionnés.
    """
    v = (version or get_signature_version()).strip()
    base = f"system/{v}"

    signature = load_prompt(f"{base}/lisa_signature.md")
    fmt = load_prompt(f"{base}/response_writer_format.md")

    return {
        "version": v,
        "signature": signature,
        "format": fmt,
    }