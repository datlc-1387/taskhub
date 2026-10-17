from functools import lru_cache

# from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "TaskHub API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://taskhub:taskhub@localhost:5432/taskhub"
    db_echo: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
