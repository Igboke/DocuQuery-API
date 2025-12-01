from fastapi import APIRouter, Depends, status, Request
from app import limiter

from app.core.security import get_api_key
from app.schemas.query import QueryRequest, QueryResponse
from app.services.query_service import QueryService
from app.dependencies import get_query_service

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
    service: QueryService = Depends(get_query_service)
):
    """
    Submits a natural language query and gets a synthesized answer
    based on the ingested knowledge base.
    """
    return service.answer_question(query_request)