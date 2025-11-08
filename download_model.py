"""
Utility script to pre-download the embedding model.
Run this once before starting Celery workers to cache the model locally.
"""
import logging
from app.core.config import settings
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_model():
    """Download and cache the embedding model."""
    logger.info(f"Downloading model to cache directory: {settings.MODEL_CACHE_DIR}")

    model = TextEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        cache_dir=settings.MODEL_CACHE_DIR
    )

    test_embeddings = list(model.embed(["test text"]))
    logger.info(f"Model downloaded successfully! Test embedding shape: {len(test_embeddings[0])}")
    logger.info(f"Model cached at: {settings.MODEL_CACHE_DIR}")

if __name__ == "__main__":
    download_model()
