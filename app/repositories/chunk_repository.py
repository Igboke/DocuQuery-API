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
        """
        stmt = select(Chunk).order_by(
            Chunk.embedding.cosine_distance(query_embedding)
        ).limit(top_k)

        return self.session.execute(stmt).scalars().all()

