import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
import enum


class DocumentStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class ChunkType(str, enum.Enum):
    text = "text"
    table = "table"
    image_caption = "image_caption"


class Document(Base):
    __tablename__ = "documents"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Which organization owns this document
    # This is the most important column — every query filters by this
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Who uploaded this document
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Original filename as uploaded by the user
    filename: Mapped[str] = mapped_column(String(500), nullable=False)

    # Full S3 path e.g. "tenants/abc123/raw/doc-uuid.pdf"
    s3_key: Mapped[str] = mapped_column(String(1000), nullable=False)

    # File type e.g. "application/pdf", "image/png"
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # File size in bytes — useful for plan limits
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Processing state — updated as the ingestion pipeline runs
    status: Mapped[DocumentStatus] = mapped_column(
        SAEnum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.pending,
    )

    # How many vector chunks were created from this document
    # Populated after ingestion completes
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Which embedding model was used
    # Important for re-indexing if we change models later
    embedding_model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Error message if processing failed
    error_message: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )

    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<Document {self.filename} ({self.status})>"