import os
import json
import httpx

from app.core.chat_logger import chat_logger
from app.settings import settings


def _join_url(base: str, path: str) -> str:
    base = (base or "").strip().rstrip("/")
    path = (path or "").strip().lstrip("/")
    if not base or not path:
        return ""
    return f"{base}/{path}"


async def fire_n8n_webhook(
    *,
    name: str,
    payload: dict,
    path_env: str,
    secret_header_name: str = "X-Webhook-Secret",
) -> None:
    if not settings.n8n_webhook_enabled:
        chat_logger.info(f"{name}.disabled")
        return

    base = (settings.n8n_webhook_base_url or "").strip()
    path = (os.getenv(path_env, "") or "").strip()
    url = _join_url(base, path)

    if not url:
        chat_logger.info(f"{name}.missing_url", base=(base or "")[:120], path_env=path_env)
        return

    timeout_ms = int(settings.n8n_webhook_timeout_ms or 1200)
    timeout_s = max(0.2, timeout_ms / 1000.0)

    headers = {"Content-Type": "application/json"}
    if settings.n8n_webhook_secret:
        headers[secret_header_name] = settings.n8n_webhook_secret

    try:
        chat_logger.info(f"{name}.call_start", url=url[:160], timeout_ms=timeout_ms)

        async with httpx.AsyncClient(timeout=timeout_s) as client:
            r = await client.post(url, content=json.dumps(payload), headers=headers)

        chat_logger.info(f"{name}.call_end", status_code=int(r.status_code))

    except Exception as e:
        chat_logger.info(f"{name}.http_error", error=str(e)[:180])