import os
from pydantic_settings import BaseSettings , SettingsConfigDict

class Settings(BaseSettings):
    """
    Application setting are read from here, it gets them from the environment variables
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    ALLOWED_FILE_EXTENSIONS: list[str] = ["zip"]

    UPLOAD_DIRECTORY = "./uploads"
    
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

    DATABASE_URL: str = os.getenv("DATABASE_URL","sqlite+aiosqlite:///./docuquery.db")

settings = Settings()
