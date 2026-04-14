from pathlib import Path

from pydantic_settings import BaseSettings

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://cdp:cdp@localhost:5432/cdp"

    # Redis / Celery
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    # LLM
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    llm_base_url: str = "https://api.anthropic.com"

    # Platform credentials
    weibo_cookie: str = ""
    douyin_cookie: str = ""

    # App
    app_name: str = "CDP - Content Distribution Platform"
    debug: bool = False
    log_level: str = "INFO"

    # Filter
    filter_batch_size: int = 100
    filter_llm_enabled: bool = True
    filter_llm_threshold: float = 0.0

    # Generator
    generator_batch_size: int = 50

    model_config = {"env_file": PROJECT_ROOT / ".env", "env_file_encoding": "utf-8"}


settings = Settings()
