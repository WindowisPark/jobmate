from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "JobMate"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://jobmate:jobmate@localhost:5432/jobmate"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # External APIs
    saramin_api_key: str = ""
    public_data_api_key: str = ""
    youtube_api_key: str = ""
    google_calendar_credentials: str = ""

    model_config = {"env_file": ".env", "env_prefix": "JOBMATE_"}


settings = Settings()
