import logging
from celery import Celery
from app.core.config import settings

logger = logging.getLogger(__name__)

celery = Celery(__name__)

celery.config_from_object(settings, namespace='CELERY')

@celery.task
def dispatch_processing_task(document_id: str):
    """
    The main entry point task (The Dispatcher).
    For now, it just logs that it received the job.
    """
    logger.info(f"[DISPATCHER] Received job for document_id: {document_id}. Routing to appropriate worker...")


@celery.task
def unpack_zip_task(document_id: str):
    """
    The specialist for unpacking zip files.
    """
    logger.info(f"[UNPACKER] Received job for document_id: {document_id}. Starting to unpack...")

@celery.task
def ingest_file_task(document_id: str, file_path: str, original_filename: str):
    """
    The specialist for ingesting a single file.
    """
    logger.info(f"[INGESTOR] Received job for document_id: {document_id}. Ingesting file: {original_filename}")
