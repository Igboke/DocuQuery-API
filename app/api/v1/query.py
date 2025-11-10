from fastapi import APIRouter, Depends, status, Request
from app import limiter
from sqlalchemy.orm import Session as SyncSession

from app.core.security import get_api_key
from app.repositories.cached_query_repository import CachedQueryRepository
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.repositories.chunk_repository import ChunkRepository
from app.core.db_sync import get_sync_db_session

router = APIRouter()

@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a question",
    dependencies=[Depends(get_api_key)]
)
@limiter.limit("5/minute")
def query_knowledgebase(
    request: Request,
    query_request: QueryRequest,
    db: SyncSession = Depends(get_sync_db_session) 
):
    """
    Submits a natural language query and gets a synthesized answer
    based on the ingested knowledge base.
    """

    chunk_repo = ChunkRepository(db)
    cached_query_repo = CachedQueryRepository(db) 
    service = QueryService(chunk_repo, cached_query_repo)
    
    response = service.answer_question(query_request)
    
    return response