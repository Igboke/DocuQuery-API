from sqlalchemy.orm import Session as SyncSession
from sqlalchemy import delete
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

