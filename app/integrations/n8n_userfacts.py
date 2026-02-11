import os
import json
import httpx

from app.core.chat_logger import chat_logger

def _env_bool(name: str, default: bool = False) -> bool:
    v = (os.getenv(name, "") or "").strip().lower()
    if v == "":
        return default
    return v in ("1", "true", "yes", "on")

def _env_int(name: str, default: int) -> int:
    try:
        return int((os.getenv(name, "") or "").strip() or default)
    except Exception:
        return default

def _get_webhook_url() -> str:
    # ✅ supporte les 2 conventions (singulier et pluriel)
    url = (os.getenv("N8N_USERFACT_WEBHOOK_URL", "") or "").strip()
    if not url:
        url = (os.getenv("N8N_USERFACTS_WEBHOOK_URL", "") or "").strip()
    return url

async def fire_userfact_webhook(payload: dict) -> None:
    enabled = _env_bool("N8N_USERFACT_WEBHOOK_ENABLED", default=True)
    if not enabled:
        chat_logger.info("userfacts.webhook.disabled")
        return

    url = _get_webhook_url()
    if not url:
        chat_logger.info("userfacts.webhook.missing_url")
        return

    timeout_ms = _env_int("N8N_USERFACT_WEBHOOK_TIMEOUT_MS", 1200)
    timeout_s = max(0.2, timeout_ms / 1000.0)

    secret = (os.getenv("N8N_USERFACTS_SECRET", "") or "").strip() or (os.getenv("N8N_USERFACT_SECRET", "") or "").strip()

    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-UserFacts-Secret"] = secret

    try:
        chat_logger.info(
            "userfacts.webhook.call_start",
            url=url[:160],
            timeout_ms=timeout_ms,
            public_user_id=str(payload.get("public_user_id")),
        )

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.post(url, content=json.dumps(payload), headers=headers)

        chat_logger.info(
            "userfacts.webhook.call_end",
            status_code=int(r.status_code),
        )

    except Exception as e:
        chat_logger.info("userfacts.webhook.http_error", error=str(e)[:180])