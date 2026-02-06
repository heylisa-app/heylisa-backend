from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ✅ Variables attendues
    environment: str = "dev"
    log_level: str = "INFO"
    database_url: str  # requis

    # ✅ Lit .env à la racine du repo
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore les variables qui traînent
        case_sensitive=False,
    )


settings = Settings()