import uuid
import datetime
from sqlalchemy import String, DateTime, Table, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from .base import Base

cached_query_chunks_link = Table(
    "cached_query_chunks_link",
    Base.metadata,
    Column("cached_query_id", ForeignKey("cached_queries.id", ondelete="CASCADE"), primary_key=True),
    Column("chunk_id", ForeignKey("chunks.id", ondelete="CASCADE"), primary_key=True),
)

class CachedQuery(Base):
    __tablename__ = "cached_queries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    question_text: Mapped[str] = mapped_column(String, nullable=False)
    question_embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    
    response_answer: Mapped[str] = mapped_column(String, nullable=False)

    source_chunks: Mapped[list["Chunk"]] = relationship(
        secondary=cached_query_chunks_link,
        back_populates="cached_queries"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc)
    )