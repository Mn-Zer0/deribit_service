from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    REDIS_URL: str
    DERIBIT_BASE_URL: str = "https://www.deribit.com/api/v2"


@lru_cache
def get_settings() -> Settings:
    return Settings()