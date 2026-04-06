from __future__ import annotations

from typing import Any, Dict

from app.integrations.n8n_webhooks import fire_n8n_webhook


async def fire_custom_request_webhook(payload: Dict[str, Any]) -> None:
    await fire_n8n_webhook(
        name="custom_request",
        payload=payload,
        path_env="N8N_CUSTOM_REQUEST_WEBHOOK_PATH",
    )