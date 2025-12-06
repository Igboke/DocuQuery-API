import aiofiles
import os
import logging
from fastapi import UploadFile
from app.repositories.document_repo import DocumentRepository
from app.models.document import Document
from app.core.config import settings
from app.worker import dispatch_processing_task

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    async def process_upload(self, file: UploadFile) -> Document:
        """
        Handles the logic for a new file upload.
        - Checks for an existing document with the same name.
        - Creates or updates the database record.
        - Saves the file to disk.
        """

        filename = file.filename
        logger.info(f"Processing upload for file: {filename}")

        if not filename:
            raise FileNotFoundError

        existing_document = await self.repository.get_by_filename(filename)

        if existing_document:
            logger.info(f"File '{filename}' already exists. Updating record for re-processing.")
            document = await self.repository.update_for_reupload(existing_document)
        else:
            logger.info(f"File '{filename}' is new. Creating new document record.")
            document = await self.repository.create_document(filename=filename)

        file_path = os.path.join(settings.UPLOAD_DIRECTORY, str(document.id) + ".zip")
        try:
            async with aiofiles.open(file_path, 'wb') as out_file:
                content = await file.read()
                await out_file.write(content)
            logger.info(f"Successfully saved file '{filename}' to '{file_path}'")
        except Exception as e:
            logger.error(f"Failed to save file '{filename}'. Error: {e}",exc_info=True)
            raise

        logger.info(f"Handing off document ID {document.id} to the background worker.")
        dispatch_processing_task.delay(str(document.id))

        return document

    async def get_document_by_id(self, document_id) -> Document | None:
        """
        Retrieves a document by its ID.
        """
        return await self.repository.get_by_id(document_id)
