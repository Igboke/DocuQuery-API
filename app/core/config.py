import os
from fastembed import TextEmbedding
import google.generativeai as genai
from prometheus_client import Histogram
from pydantic_settings import BaseSettings, SettingsConfigDict

os.environ['HF_HUB_OFFLINE'] = '1'


class Settings(BaseSettings):
    """
    Application setting are read from here, it gets them from the environment variables
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding='utf-8')

    DB_USER: str = os.getenv("DB_USER", "")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = 5432
    DB_NAME: str = os.getenv("DB_NAME", "name")

    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))

    ALLOWED_FILE_EXTENSIONS: list[str] = ["zip"]

    UPLOAD_DIRECTORY: str = "./uploads"

    MODEL_CACHE_DIR: str = "./model_cache"

    MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    os.makedirs(MODEL_CACHE_DIR, exist_ok=True)

    DATABASE_URL: str = os.getenv("DATABASE_URL","sqlite+aiosqlite:///./docuquery.db")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def CELERY_BROKER_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    TEST_DATABASE_URL: str = os.getenv("TEST_DATABASE_URL","sqlite+aiosqlite:///./docuquery.db")

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "default_key")

    API_KEY: str = os.getenv("API_KEY", "default_key")


settings = Settings()

genai.configure(api_key=settings.GOOGLE_API_KEY)

_embedding_model = None
_generative_model = None

def get_embedding_model():
    """
    Lazy initialization of the embedding model.
    This ensures the model is loaded only once and only when needed.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = TextEmbedding(
            model_name=settings.MODEL_NAME,
            cache_dir=settings.MODEL_CACHE_DIR
        )
    return _embedding_model

def get_generative_model():
    """
    Lazy initialization of the Gemini generative model.
    """
    global _generative_model
    if _generative_model is None:
        _generative_model = genai.GenerativeModel('gemini-2.5-flash')
    return _generative_model

LLM_QUERY_DURATION = Histogram(
    "llm_query_duration_seconds",
    "Histogram of the duration of LLM API calls in seconds."
)
