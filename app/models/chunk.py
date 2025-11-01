import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from .base import Base

class Chunk(Base):
    __tablename__= "chunks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"))
    chunk_text: Mapped[str] = mapped_column(String, nullable=False)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    document = relationship("Document", back_populates="chunks")