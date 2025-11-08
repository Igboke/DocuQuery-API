import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application setting are read from here, it gets them from the environment variables
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    ALLOWED_FILE_EXTENSIONS: list[str] = ["zip"]

    UPLOAD_DIRECTORY: str = "./uploads"

    MODEL_CACHE_DIR: str = "./model_cache"

    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

    DATABASE_URL: str = os.getenv("DATABASE_URL","sqlite+aiosqlite:///./docuquery.db")

    CELERY_BROKER_URL: str = "redis://localhost:6379/0"

    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL","sqlite+aiosqlite:///./docuquery.db")


settings = Settings()
