from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from app.models import CachedQuery
from app.models.chunk import Chunk
from typing import List

SIMILARITY_THRESHOLD = 0.70



class CachedQueryRepository:
    def __init__(self, session: SyncSession):
        self.session = session

    def find_similar_query(self, query_embedding: List[float]) -> CachedQuery | None:
        """
        Finds a cached query if its embedding is within the similarity threshold.
        This is done in a single, efficient query.
        """

        distance_threshold = 1 - SIMILARITY_THRESHOLD

        stmt = text("""
            SELECT id
            FROM cached_queries
            WHERE (question_embedding <=> CAST(:query_embedding AS vector)) < :distance_threshold
            ORDER BY question_embedding <=> CAST(:query_embedding AS vector)
            LIMIT 1
        """)
        
        result = self.session.execute(
            stmt,
            {
                "query_embedding": query_embedding,
                "distance_threshold": distance_threshold
            }
        ).scalar_one_or_none()

        if result:
            similar_query_id = result
            final_stmt = select(CachedQuery).options(
                selectinload(CachedQuery.source_chunks)
            ).where(CachedQuery.id == similar_query_id)
            
            return self.session.execute(final_stmt).scalar_one_or_none()

        return None

    def save_query(self, question_text: str, query_embedding: list[float], answer: str, source_chunks: list[Chunk]):
        """Saves a new query and links it to its source chunks."""
        new_cached_query = CachedQuery(
            question_text=question_text,
            question_embedding=query_embedding,
            response_answer=answer,
            source_chunks=source_chunks
        )
        self.session.add(new_cached_query)