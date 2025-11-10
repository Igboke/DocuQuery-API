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
