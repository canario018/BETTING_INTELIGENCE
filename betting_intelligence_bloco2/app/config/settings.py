from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{DATA_DIR / 'betting.db'}"
    log_level: str = "INFO"
    idempotency_window_seconds: int = 60
    collectors: str = "fixture"
    betano_api_endpoint: str = ""
    superbet_api_endpoint: str = ""
    novibet_api_endpoint: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
