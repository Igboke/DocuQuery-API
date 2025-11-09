from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import delete, text
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
        Finds the top_k most relevant chunks using cosine similarity.
        """

        stmt = text("""
            SELECT id, document_id, chunk_text, chunk_metadata, embedding
            FROM chunks
            ORDER BY embedding <=> :query_embedding
            LIMIT :top_k
        """)
        
        result = self.session.execute(
            stmt,
            {"query_embedding": str(query_embedding), "top_k": top_k}
        )
        
        chunks = []
        for row in result.mappings():
            chunks.append(Chunk(**row))
            
        return chunks

