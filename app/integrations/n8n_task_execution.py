from __future__ import annotations

from typing import Any, Dict

from app.integrations.n8n_webhooks import fire_n8n_webhook


async def fire_task_execution_webhook(payload: Dict[str, Any]) -> None:
    await fire_n8n_webhook(
        name="task_execution",
        payload=payload,
        path_env="N8N_TASK_EXECUTION_WEBHOOK_PATH",
    )