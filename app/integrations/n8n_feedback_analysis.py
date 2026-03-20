from __future__ import annotations

from typing import Any, Dict

from app.integrations.n8n_webhooks import fire_n8n_webhook


async def fire_feedback_analysis_webhook(payload: Dict[str, Any]) -> None:
    await fire_n8n_webhook(
        name="feedback_analysis",
        payload=payload,
        path_env="N8N_FEEDBACK_ANALYSIS_WEBHOOK_PATH",
    )