from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import Document,IngestionStatus

class DocumentRepository:
    """
    Handles the database operations for the Document model.
    """
    def __init__(self,session:AsyncSession):
        self.session = session

    async def get_by_filename(self,filename:str|None)-> Document | None:
        """
        Returns a document by filename if it exists
        """

        result = await self.session.execute(select(Document).where(Document.filename == filename))
        return result.scalars().first()

    async def create_document(self, filename: str|None) -> Document:
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