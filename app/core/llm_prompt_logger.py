# app/core/llm_prompt_logger.py
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, List, Optional

from app.core.chat_logger import chat_logger


def _env_on(name: str, default: str = "0") -> bool:
    v = (os.getenv(name) or default).strip().lower()
    return v in ("1", "true", "yes", "on")


def log_llm_messages(
    *,
    event: str,
    messages: List[Dict[str, Any]],
    trace: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log les messages LLM COMPLETS en chunks pour éviter la troncature Railway.
    Usage:
      log_llm_messages(event="llm.prompt.response_writer", messages=[...], trace={...}, extra={...})

    Contrôle via env:
      - LOG_LLM_PROMPTS=1 : active
      - LOG_LLM_PROMPTS_FULL=1 : log le contenu (sinon juste meta)
      - LOG_LLM_PROMPTS_CHUNK_SIZE=3500 : taille des chunks
    """
    if not _env_on("LOG_LLM_PROMPTS", "0"):
        return

    trace = trace or {}
    extra = extra or {}

    # Nettoyage minimal (éviter objets non sérialisables)
    safe_msgs = []
    for m in (messages or []):
        if not isinstance(m, dict):
            continue
        role = str(m.get("role") or "")
        content = m.get("content")
        if content is None:
            content = ""
        safe_msgs.append({"role": role, "content": str(content)})

    payload = {
        "messages": safe_msgs,
        "trace": trace,
        "extra": extra,
    }

    blob = json.dumps(payload, ensure_ascii=False)
    sha = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    total_len = len(blob)

    chunk_size = int((os.getenv("LOG_LLM_PROMPTS_CHUNK_SIZE") or "3500").strip() or "3500")
    chunk_size = max(800, min(chunk_size, 12000))  # bornes safe

    full_on = _env_on("LOG_LLM_PROMPTS_FULL", "0")

    # 1) Header (toujours)
    chat_logger.info(
        event,
        llm_prompt_sha256=sha,
        llm_prompt_len=total_len,
        llm_messages_count=len(safe_msgs),
        llm_full_enabled=full_on,
        **{k: v for k, v in trace.items() if k is not None},
        **{f"extra_{k}": v for k, v in extra.items() if k is not None},
    )

    # 2) Chunks (seulement si FULL)
    if not full_on:
        return

    chunks = [blob[i : i + chunk_size] for i in range(0, total_len, chunk_size)]
    total = len(chunks)

    for i, ch in enumerate(chunks, start=1):
        chat_logger.info(
            f"{event}.chunk",
            llm_prompt_sha256=sha,
            chunk_index=i,
            chunk_total=total,
            chunk=ch,
            **{k: v for k, v in trace.items() if k is not None},
        )