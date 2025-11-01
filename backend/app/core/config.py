"""
Application configuration using Pydantic settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str

    # MinIO S3-compatible storage
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "resumes"
    MINIO_SECURE: bool = False

    # Email (SMTP)
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "AlmaLead"

    # JWT Authentication
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours

    # Attorney Account (for seeding)
    ATTORNEY_EMAIL: str
    ATTORNEY_PASSWORD: str
    ATTORNEY_FIRST_NAME: str = "John"
    ATTORNEY_LAST_NAME: str = "Attorney"

    # File Upload
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: list[str] = [".pdf", ".doc", ".docx"]

    # Application
    APP_NAME: str = "AlmaLead"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
