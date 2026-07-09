from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    environment: str = "production"
    secret_key: str
    allowed_origins: str = "https://lookla.gr,https://www.lookla.gr"
    admin_email: str = "columb@europe.com"

    # Database
    db_user: str
    db_password: str
    db_host: str = "db"
    db_port: int = 5432
    db_name: str = "beauty_gr"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Media (Cloudflare R2)
    r2_account_id: str = ""
    r2_access_key: str = ""
    r2_secret_key: str = ""
    r2_bucket: str = "lookla-photos"
    r2_endpoint: str = ""
    r2_cdn_url: str = "https://cdn.lookla.gr"
    r2_public_url: str = "https://cdn.lookla.gr"  # legacy alias

    # Email (Resend)
    resend_api_key: str = ""
    resend_sender_email: str = "noreply@lookla.gr"
    resend_sender_name: str = "Lookla"

    # Moderation
    openai_api_key: str = ""
    google_vision_api_key: str = ""

    # Payments
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    payment_provider: str = "stripe"

    # Auth
    google_client_id: str = ""
    google_client_secret: str = ""

    # Turnstile
    turnstile_secret_key: str = ""

    # Sentry
    sentry_dsn: str = ""

    # JWT
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    class Config:
        env_file = "/root/beauty-gr/.env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
