import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import logging
from app.core.database import get_uow
from app.core.config import settings
from app.repositories.document_repo import DocumentRepository
from app.services.document_service import DocumentService
from app.schemas.document import DocumentJob

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/documents/upload",
    response_model=DocumentJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a knowledge base"
)
async def upload_documents(
    file: UploadFile = File(..., description="A file for the knowledge base."),
    session: AsyncSession = Depends(get_uow)
):
    """
    Accepts a file for asynchronous processing.
    """
    file_extension = file.filename.split(".")[-1] if "." in file.filename else ""
    if file_extension not in settings.ALLOWED_FILE_EXTENSIONS:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types are: {', '.join(settings.ALLOWED_FILE_EXTENSIONS)}"
        )
    repo = DocumentRepository(session)
    service = DocumentService(repo)

    try:
        document = await service.process_upload(file)

    except Exception as e:
        logger.exception("Error at upload document",exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the file: {e}"
        ) from e
    
    return DocumentJob(job_id=document.id, filename=document.filename, status=document.status)

@router.get(
    "/documents/{job_id}/status",
    response_model=DocumentJob,
    summary="Get ingestion job status"
)
async def get_job_status(
    job_id: uuid.UUID,
    session: AsyncSession = Depends(get_uow)
):
    """
    Retrieves the current status of a document processing job.
    """
    repo = DocumentRepository(session)

    document = await repo.get_by_id(job_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found."
        )
    
    return DocumentJob(job_id=document.id, filename=document.filename, status=document.status)