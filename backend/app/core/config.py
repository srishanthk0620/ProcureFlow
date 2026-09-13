from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    APP_NAME: str = "ProcureFlow API"
    APP_ENV: str = "development"
    DATABASE_URL: str = "sqlite:///./procureflow.db"
    AUTH_OTP_SECRET: SecretStr | None = None
    OTP_TTL_SECONDS: int = Field(default=300, ge=60, le=600)
    SESSION_TTL_SECONDS: int = Field(default=3600, ge=60, le=86400)
    DEV_CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]


settings = Settings()
