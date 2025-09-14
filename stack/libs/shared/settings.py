import os
from dataclasses import dataclass


@dataclass
class Settings:
    env: str = os.getenv("ENV", "local")
    sentry_dsn: str | None = os.getenv("SENTRY_DSN")
    db_url: str | None = os.getenv("DATABASE_URL")


settings = Settings()
