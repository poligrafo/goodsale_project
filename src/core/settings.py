from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_HOST: str
    DATABASE_PORT: int
    ELASTICSEARCH_URL: str
    XML_FEED_URL: str
    LOG_DIR: Path = Path(__file__).resolve().parent.parent.parent / "logs"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
