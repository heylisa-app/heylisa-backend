from app.integrations.n8n_webhooks import fire_n8n_webhook

async def fire_userfact_webhook(payload: dict) -> None:
    await fire_n8n_webhook(
        name="userfacts.webhook",
        payload=payload,
        path_env="N8N_USERFACT_WEBHOOK_PATH",
        secret_header_name="X-UserFacts-Secret",
    )