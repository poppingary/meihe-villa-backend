"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Meihe Villa API"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/meihe_villa"

    # JWT Authentication
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Cookie settings
    cookie_domain: str = ""  # Empty for localhost
    cookie_secure: bool = False  # Set True in production (HTTPS only)
    cookie_samesite: str = "lax"
    access_token_expire_hours: int = 24

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # AWS S3 - Environment-based configuration
    environment: str = "dev"  # "dev" or "prod"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-northeast-1"

    # Dev environment (Asia)
    s3_bucket_dev: str = "meihe-villa-media-asia-dev"
    cloudfront_domain_dev: str = ""

    # Prod environment (Asia)
    s3_bucket_prod: str = "meihe-villa-media-asia"
    cloudfront_domain_prod: str = "d34s20t5chx0dl.cloudfront.net"

    # Pre-signed URL expiration (seconds)
    presigned_url_expiration: int = 3600  # 1 hour

    @property
    def s3_bucket_name(self) -> str:
        """Get S3 bucket name based on environment."""
        return self.s3_bucket_prod if self.environment == "prod" else self.s3_bucket_dev

    @property
    def cloudfront_domain(self) -> str:
        """Get CloudFront domain based on environment."""
        if self.environment == "prod":
            return self.cloudfront_domain_prod
        return self.cloudfront_domain_dev

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
