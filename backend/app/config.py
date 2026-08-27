import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_FLASH_MODEL: str = "gemini-2.5-flash"
    GEMINI_PRO_MODEL: str = "gemini-2.5-pro"
    MONGODB_URI: str = ""
    MONGODB_DB_NAME: str = "vigilnet"
    REDIS_URL: str = "redis://localhost:6379"
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = ""

    model_config = SettingsConfigDict(
        # Try reading .env file from either root or backend folder
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
