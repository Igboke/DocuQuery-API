from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session as SyncSession

from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.repositories.chunk_repository import ChunkRepository
from app.core.db_sync import get_sync_db_session

router = APIRouter()

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question"
)
def query_knowledgebase(
    request: QueryRequest,
    db: SyncSession = Depends(get_sync_db_session) 
):
    """
    Submits a natural language query and gets a synthesized answer
    based on the ingested knowledge base.
    """

    chunk_repo = ChunkRepository(db)
    service = QueryService(chunk_repo)
    
    response = service.answer_question(request)
    
    return response