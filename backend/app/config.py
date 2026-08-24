import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
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
