from __future__ import annotations

from typing import Any, Dict

from app.integrations.n8n_webhooks import fire_n8n_webhook


async def fire_followup_after_info_collected_webhook(
    payload: Dict[str, Any],
) -> None:
    await fire_n8n_webhook(
        name="followup_after_info_collected",
        payload=payload,
        path_env="N8N_FOLLOWUP_AFTER_INFO_COLLECTED_WEBHOOK_PATH",
    )