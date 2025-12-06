"""
Dependency injection configuration for FastAPI endpoints.
Provides properly wired services and repositories without exposing database sessions to handlers.
"""
from fastapi import Depends
from sqlalchemy.orm import Session as SyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.db_sync import get_sync_db_session
from app.core.database import get_session
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.cached_query_repository import CachedQueryRepository
from app.repositories.document_repo import DocumentRepository
from app.services.query_service import QueryService
from app.services.document_service import DocumentService
from app.services.health_service import HealthService

limiter = Limiter(key_func=get_remote_address)



def get_query_service(
    db: SyncSession = Depends(get_sync_db_session)
) -> QueryService:
    """
    Provides a fully configured QueryService with all its dependencies.
    Handlers depend on this instead of constructing services manually.
    """
    chunk_repo = ChunkRepository(db)
    cached_query_repo = CachedQueryRepository(db)
    return QueryService(chunk_repo, cached_query_repo)


def get_document_service(
    session: AsyncSession = Depends(get_session)
) -> DocumentService:
    """
    Provides a fully configured DocumentService with all its dependencies.
    """
    document_repo = DocumentRepository(session)
    return DocumentService(document_repo)


def get_health_service(
    session: AsyncSession = Depends(get_session)
) -> HealthService:
    """
    Provides a fully configured HealthService.
    """
    return HealthService(session)
