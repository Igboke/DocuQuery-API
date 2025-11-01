from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_uow
from app.core.config import settings
from app.repositories.document_repo import DocumentRepository
from app.services.document_service import DocumentService
from app.schemas.document import DocumentJob

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the file: {e}"
        ) from e
    
    return DocumentJob(job_id=document.id, filename=document.filename, status=document.status)