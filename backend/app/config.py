import json
import re
from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AI News Intelligence & Sentiment Radar"
    api_prefix: str = "/api/v1"

    # Supabase/Postgres URL (recommended for production and Vercel)
    database_url: str = "sqlite:///./news_radar.db"
    auto_create_tables: bool = True

    rss_feeds: Annotated[list[str], NoDecode] = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
    ]
    max_articles_per_feed: int = 25
    ingest_interval_minutes: int = 30
    digest_hour_24: int = 18
    timezone: str = "UTC"
    enable_local_scheduler: bool = False

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    gmail_username: str = ""
    gmail_app_password: str = ""
    gmail_smtp_host: str = "smtp.gmail.com"
    gmail_smtp_port: int = 465
    alert_recipients: Annotated[list[str], NoDecode] = []
    digest_recipients: Annotated[list[str], NoDecode] = []
    alert_sentiment_threshold: float = -0.6

    cron_secret: str = ""

    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator(
        "rss_feeds",
        "alert_recipients",
        "digest_recipients",
        "cors_origins",
        mode="before",
    )
    @classmethod
    def parse_csv_values(cls, value):
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return []
            if raw.startswith("["):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in raw.split(",") if item.strip()]
        return value

    @field_validator("digest_hour_24")
    @classmethod
    def validate_digest_hour(cls, value: int) -> int:
        if value < 0 or value > 23:
            raise ValueError("DIGEST_HOUR_24 must be between 0 and 23.")
        return value

    @field_validator("ingest_interval_minutes")
    @classmethod
    def validate_ingest_interval(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("INGEST_INTERVAL_MINUTES must be greater than 0.")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url_percent_encoding(cls, value: str) -> str:
        # Common setup issue: unencoded '%' in DB passwords breaks URI parsing/authentication.
        if isinstance(value, str) and re.search(r"%(?![0-9A-Fa-f]{2})", value):
            raise ValueError(
                "DATABASE_URL contains invalid percent-encoding. "
                "URL-encode password special characters or use an alphanumeric password."
            )
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
