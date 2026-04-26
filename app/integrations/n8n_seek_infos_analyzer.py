from __future__ import annotations

from typing import Any, Dict

from app.integrations.n8n_webhooks import fire_n8n_webhook


async def fire_seek_infos_analyzer_webhook(payload: Dict[str, Any]) -> None:
    await fire_n8n_webhook(
        name="seek_infos_analyzer",
        payload=payload,
        path_env="N8N_SEEK_INFOS_ANALYZER_WEBHOOK_PATH",
    )