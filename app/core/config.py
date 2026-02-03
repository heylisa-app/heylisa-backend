from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "dev"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
