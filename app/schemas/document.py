import uuid
from pydantic import BaseModel, ConfigDict
from app.models.document import IngestionStatus

class DocumentJob(BaseModel):
    """
    The response model for a document upload job.
    """
    job_id: uuid.UUID
    filename: str
    status: IngestionStatus

    model_config = ConfigDict(from_attributes=True)