from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import delete, text, select
from app.models import Chunk, Document

class ChunkRepository:
    def __init__(self, session: SyncSession):

        self.session = session

    def delete_by_document_id_sync(self, document_id: str):
        """
        Synchronously deletes all chunks associated with a given document ID.
        """
        self.session.execute(
            delete(Chunk).where(Chunk.document_id == document_id)
        )

    def find_relevant_chunks_sync(self, query_embedding: list[float], top_k: int = 5) -> list[Chunk]:
        """
        Finds the most relevant chunks using vector similarity.

        Strategy: Use raw SQL for fast vector search to get IDs only,
        then fetch via ORM to get properly-attached objects that can be used in relationships.
        """
 
        stmt = text("""
            SELECT id
            FROM chunks
            ORDER BY embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
        """)

        result = self.session.execute(
            stmt,
            {"query_embedding": query_embedding.tolist() if hasattr(query_embedding, 'tolist') else query_embedding, "top_k": top_k}
        )

        chunk_ids = [row[0] for row in result]

        if not chunk_ids:
            return []

        chunks = self.session.execute(
            select(Chunk).where(Chunk.id.in_(chunk_ids))
        ).scalars().all()

        chunks_dict = {chunk.id: chunk for chunk in chunks}
        return [chunks_dict[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks_dict]

