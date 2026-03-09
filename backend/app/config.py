from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    news_api_key: str = ""
    guardian_api_key: str = ""

    database_url: str = "postgresql://postgres:password@db:5432/newsagg"
    redis_url: str = "redis://redis:6379/0"

    ingestion_interval_minutes: int = 30
    max_political_articles: int = 5
    max_positive_articles: int = 50
    refresh_api_key: str = "change-me-in-production"


settings = Settings()
