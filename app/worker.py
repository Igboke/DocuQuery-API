import logging
import os
import tempfile
import zipfile
from celery import Celery, chord
from app.core.config import settings
from app.core.db_sync import get_sync_db
from langchain_text_splitters import RecursiveCharacterTextSplitter
from fastembed import TextEmbedding
from app.models import Chunk
from app.models.document import IngestionStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repo import DocumentRepository

logger = logging.getLogger(__name__)

os.environ['HF_HUB_OFFLINE'] = '1'

_embedding_model = None

def get_embedding_model():
    """
    Lazy initialization of the embedding model.
    This ensures the model is loaded once per worker process.
    """
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"[WORKER] Initializing embedding model from cache: {settings.MODEL_CACHE_DIR}")
        _embedding_model = TextEmbedding(
            model_name=settings.MODEL_NAME,
            cache_dir=settings.MODEL_CACHE_DIR
        )
        logger.info("[WORKER] Embedding model initialized successfully.")
    return _embedding_model

celery = Celery(__name__)

celery.config_from_object(settings, namespace='CELERY')

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
chunk_size=500,
chunk_overlap=50,
length_function=len,
)

@celery.task
def dispatch_processing_task(document_id: str):
    """
    The main entry point task (The Dispatcher).
    For now, it just logs that it received the job.
    """
    logger.info(f"[DISPATCHER] Received job for document_id: {document_id}. Routing to appropriate worker...")

    with get_sync_db() as db:
        repo = DocumentRepository(db)
        
        document = repo.get_by_id_sync(document_id)

        if not document:
            logger.error(f"[DISPATCHER] Document with ID {document_id} not found. Aborting.")
            return

        repo.update_status_sync(document, status=IngestionStatus.PROCESSING)
        logger.info(f"[DISPATCHER] Document '{document.filename}' status set to PROCESSING.")

        if document.filename.endswith('.zip'):
            logger.info(f"[DISPATCHER] Routing '{document.filename}' to the Unpacker worker.")
            unpack_zip_task.delay(document_id)
        
        elif document.filename.endswith('.md'):
            logger.info(f"[DISPATCHER] Routing '{document.filename}' directly to the Ingestor worker.")
            file_path = f"./uploads/{document.id}.md"
            ingest_file_task.delay(document_id, file_path, document.filename)
        
        else:
            error_msg = f"Unsupported file type: {document.filename}"
            logger.error(f"[DISPATCHER] {error_msg}")
            repo.update_status_sync(document, status=IngestionStatus.FAILED, error_message=error_msg)


@celery.task
def unpack_zip_task(document_id: str):
    """
    The specialist for unpacking zip files.
    """
    logger.info(f"[UNPACKER] Received job for document_id: {document_id}. Starting to unpack...")

    with get_sync_db() as db:
        doc_repo = DocumentRepository(db)
        chunk_repo = ChunkRepository(db)
        
        document = doc_repo.get_by_id_sync(document_id)
        if not document:
            logger.error(f"[UNPACKER] Document {document_id} not found.")
            return

        logger.info(f"[UNPACKER] Deleting old chunks for document {document_id}.")
        chunk_repo.delete_by_document_id_sync(document_id)
        db.commit() 

        file_path = f"./uploads/{document.id}.zip"
        ingest_tasks = []
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                logger.info(f"[UNPACKER] Fanning out tasks for files in {document.filename}")
                for filename in os.listdir(temp_dir):
                    if filename.endswith('.md'):
                        full_path = os.path.join(temp_dir, filename)
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        ingest_tasks.append(ingest_file_task.s(document_id, content, filename))
        except Exception as e:
            logger.exception("[UNPACKER] Failed to unpack or prepare tasks.")
            doc_repo.update_status_sync(document, IngestionStatus.FAILED, str(e))
            return

        if not ingest_tasks:
            logger.warning(f"[UNPACKER] No .md files found in {document.filename}. Marking as complete.")
            doc_repo.update_status_sync(document, IngestionStatus.COMPLETED)
            return

        callback = finalize_processing_task.s(document_id = document_id)
        chord(ingest_tasks)(callback)

        logger.info(f"[UNPACKER] Dispatched {len(ingest_tasks)} ingest jobs with a finalization callback.")

@celery.task
def finalize_processing_task(results,document_id: str):
    """
    The callback task that marks a document as COMPLETED.
    """
    logger.info(f"[FINALIZER] All ingest jobs complete for document {document_id}. Setting status to COMPLETED.")
    with get_sync_db() as db:
        repo = DocumentRepository(db)
        document = repo.get_by_id_sync(document_id)
        if document:
            repo.update_status_sync(document, IngestionStatus.COMPLETED)

@celery.task
def ingest_file_task(document_id: str, file_content: str, original_filename: str):
    """
    The specialist for ingesting a single file.
    Receives the file's text content directly.
    """
    logger.info(f"[INGESTOR] Ingesting content from '{original_filename}' for document {document_id}.")
    
    try:
        text = file_content

        chunks_text = TEXT_SPLITTER.split_text(text)
        logger.info(f"[INGESTOR] Split '{original_filename}' into {len(chunks_text)} chunks.")

        embedding_model = get_embedding_model()
        embeddings = list(embedding_model.embed(chunks_text))
        logger.info(f"[INGESTOR] Created {len(embeddings)} embeddings.")

        chunks_to_create = []
        for i, text_chunk in enumerate(chunks_text):
            chunk = Chunk(
                document_id=document_id,
                chunk_text=text_chunk,
                embedding=embeddings[i],
                chunk_metadata={
                    "source_filename": original_filename,
                    "chunk_index": i
                }
            )
            chunks_to_create.append(chunk)

        with get_sync_db() as db:
            db.bulk_save_objects(chunks_to_create)
            db.commit()
        
        logger.info(f"[INGESTOR] Successfully saved {len(chunks_to_create)} chunks to the database.")

    except Exception as e:
        logger.exception(f"[INGESTOR] Failed to ingest file '{original_filename}'.", exc_info=True)
