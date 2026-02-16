from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    environment: str = Field(default="dev", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Database
    database_url: str = Field(alias="DATABASE_URL")

    # Supabase auth (optional in dev, required in prod later)
    supabase_url: str | None = Field(default=None, alias="SUPABASE_URL")
    supabase_anon_key: str | None = Field(default=None, alias="SUPABASE_ANON_KEY")

    # LLM
    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_base_url: str = Field(default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model_fallback: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL_FALLBACK")
    openai_base_url: str = Field(default="https://api.openai.com", alias="OPENAI_BASE_URL")

    # n8n (global webhooks config)
    n8n_webhook_base_url: str | None = Field(default=None, alias="N8N_WEBHOOK_BASE_URL")
    n8n_webhook_enabled: bool = Field(default=True, alias="N8N_WEBHOOK_ENABLED")
    n8n_webhook_timeout_ms: int = Field(default=1200, alias="N8N_WEBHOOK_TIMEOUT_MS")
    n8n_webhook_secret: str | None = Field(default=None, alias="N8N_WEBHOOK_SECRET")

    # n8n paths (1 env var per webhook event)
    n8n_userfact_webhook_path: str | None = Field(default=None, alias="N8N_USERFACT_WEBHOOK_PATH")


settings = Settings()