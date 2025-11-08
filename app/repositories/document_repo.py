from datetime import datetime, timezone
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session as SyncSession
from app.models.document import Document, IngestionStatus


class DocumentRepository:
    """
    Handles the database operations for the Document model.
    """
    def __init__(self, session: AsyncSession | SyncSession):
        self.session = session

    async def get_by_filename(self, filename: str | None) -> Document | None:
        """
        Returns a document by filename if it exists
        """

        result = await self.session.execute(select(Document).where(Document.filename == filename))
        return result.scalars().first()
    
    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Asynchronously retrieves a document by its ID."""
        return await self.session.get(Document, document_id)

    async def create_document(self, filename: str | None) -> Document:
        """
        Creates a new document record in the database with PENDING status.

        Args:
            filename: The original name of the uploaded file.

        Returns:
            The newly created Document object.
         """
        
        new_document = Document(filename=filename)
        self.session.add(new_document)
        await self.session.flush()
        await self.session.refresh(new_document)
        
        return new_document
    
    async def update_for_reupload(self, document: Document) -> Document:
        """
        update the document for reupload
        """
        document.status = IngestionStatus.PENDING
        document.error_message = None
        await self.session.flush()
        await self.session.refresh(document)
        return document
    
    def get_by_id_sync(self, document_id: str) -> Document | None:
        """Synchronously retrieves a document by its ID."""
        return self.session.get(Document, document_id)
    
    def update_status_sync(self, document: Document, status: IngestionStatus, error_message: str | None = None) -> Document:
        """Synchronously updates a document's status and error message."""
        document.status = status
        document.error_message = error_message
        document.updated_at = datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(document)
        return document