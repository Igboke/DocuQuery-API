import logging
import os
import tempfile
import zipfile
from celery import Celery, chord
from app.core.config import settings, get_embedding_model
from app.core.db_sync import get_sync_db
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models import Chunk
from app.models.document import IngestionStatus
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repo import DocumentRepository

logger = logging.getLogger(__name__)

os.environ['HF_HUB_OFFLINE'] = '1'

celery = Celery(__name__)

celery.config_from_object(settings, namespace='CELERY')

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
chunk_size=2000,
chunk_overlap=200,
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
    Extracts files to a persistent temporary location and passes file paths to ingest tasks
    to avoid serializing large content in Celery messages.
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
        

        temp_extract_dir = f"./uploads/temp_{document_id}"
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        ingest_tasks = []
        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            logger.info(f"[UNPACKER] Fanning out tasks for files in {document.filename}")
            for filename in os.listdir(temp_extract_dir):
                if filename.endswith('.md'):
                    full_path = os.path.join(temp_extract_dir, filename)

                    ingest_tasks.append(ingest_file_from_path_task.s(document_id, full_path, filename))
                    
            logger.info(f"[UNPACKER] Created {len(ingest_tasks)} ingest tasks for files in temp directory: {temp_extract_dir}")
            
        except Exception as e:
            logger.exception("[UNPACKER] Failed to unpack or prepare tasks.")
            doc_repo.update_status_sync(document, IngestionStatus.FAILED, str(e))

            if os.path.exists(temp_extract_dir):
                import shutil
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return

        if not ingest_tasks:
            logger.warning(f"[UNPACKER] No .md files found in {document.filename}. Marking as complete.")
            doc_repo.update_status_sync(document, IngestionStatus.COMPLETED)

            if os.path.exists(temp_extract_dir):
                import shutil
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            return

        callback = finalize_processing_task.s(document_id=document_id, temp_dir=temp_extract_dir)
        chord(ingest_tasks)(callback)

        logger.info(f"[UNPACKER] Dispatched {len(ingest_tasks)} ingest jobs with a finalization callback.")

@celery.task
def finalize_processing_task(results: list, document_id: str, temp_dir: str = None):
    """
    The callback task that inspects the results of all ingest tasks
    and sets the final status for the parent Document.
    Also cleans up the temporary directory used for extracted files.
    """
    logger.info(f"[FINALIZER] All ingest jobs finished for document {document_id}. Analyzing results...")
    
    failed_files = []
    for result in results:
        if result and result.get("status") == "FAILED":
            failed_files.append(result)

    with get_sync_db() as db:
        repo = DocumentRepository(db)
        document = repo.get_by_id_sync(document_id)
        if not document:
            logger.error(f"[FINALIZER] Document {document_id} not found. Cannot set final status.")
            return

        if failed_files:
            error_messages = [f"  - {f.get('filename')}: {f.get('error', 'Unknown error')}" for f in failed_files]
            full_error_message = f"Ingestion failed for {len(failed_files)} file(s):\n" + "\n".join(error_messages)
            
            logger.error(f"[FINALIZER] Job for document {document_id} failed. Details:\n{full_error_message}")
            repo.update_status_sync(document, IngestionStatus.FAILED, full_error_message)
        else:
            logger.info(f"[FINALIZER] All {len(results)} files ingested successfully for document {document_id}. Setting status to COMPLETED.")
            repo.update_status_sync(document, IngestionStatus.COMPLETED)
    
    if temp_dir and os.path.exists(temp_dir):
        try:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.info(f"[FINALIZER] Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"[FINALIZER] Failed to clean up temp directory {temp_dir}: {e}")

@celery.task
def ingest_file_from_path_task(document_id: str, file_path: str, original_filename: str):
    """
    The specialist for ingesting a single file from a file path.
    Reads content from disk to avoid large message serialization.
    Uses batched processing to prevent out-of-memory errors.
    """
    logger.info(f"[INGESTOR] Ingesting file from '{file_path}' (original: '{original_filename}') for document {document_id}.")
    
    BATCH_SIZE = 500
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        chunks_text = TEXT_SPLITTER.split_text(text)
        total_chunks = len(chunks_text)
        logger.info(f"[INGESTOR] Split '{original_filename}' into {total_chunks} chunks. Processing in batches of {BATCH_SIZE}...")

        embedding_model = get_embedding_model()
        total_saved = 0
        
        for batch_start in range(0, total_chunks, BATCH_SIZE):
            batch_end = min(batch_start + BATCH_SIZE, total_chunks)
            batch_chunks = chunks_text[batch_start:batch_end]
            
            logger.info(f"[INGESTOR] Processing batch {batch_start}-{batch_end} of {total_chunks} chunks...")
            
            
            batch_embeddings = list(embedding_model.embed(batch_chunks))
            
            
            chunks_to_create = []
            for i, text_chunk in enumerate(batch_chunks):
                chunk = Chunk(
                    document_id=document_id,
                    chunk_text=text_chunk,
                    embedding=batch_embeddings[i].tolist(),
                    chunk_metadata={
                        "source_filename": original_filename,
                        "chunk_index": batch_start + i
                    }
                )
                chunks_to_create.append(chunk)
            
            
            with get_sync_db() as db:
                db.bulk_save_objects(chunks_to_create)
                db.commit()
            
            total_saved += len(chunks_to_create)
            logger.info(f"[INGESTOR] Saved batch to database. Progress: {total_saved}/{total_chunks} chunks ({total_saved*100//total_chunks}%)")
        
        logger.info(f"[INGESTOR] Successfully saved all {total_saved} chunks to the database.")

        return {"status": "SUCCESS", "filename": original_filename}

    except Exception as e:
        logger.exception(f"[INGESTOR] Failed to ingest file '{original_filename}' from path '{file_path}'.", exc_info=True)

        return {"status": "FAILED", "filename": original_filename, "error": str(e)}

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
                embedding=embeddings[i].tolist(),
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

        return {"status": "SUCCESS", "filename": original_filename}

    except Exception as e:
        logger.exception(f"[INGESTOR] Failed to ingest file '{original_filename}'.", exc_info=True)

        return {"status": "FAILED", "filename": original_filename, "error": str(e)}
