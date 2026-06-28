import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Which organization made this query
    # Indexed because we query logs by org very frequently
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Which user asked the question
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # SHA-256 hash of the question
    # We store the hash not the raw text for privacy
    # Also used as Redis cache key
    question_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    # The actual question — stored for debugging and analytics
    question_text: Mapped[str] = mapped_column(Text, nullable=False)

    # How long the full query took in milliseconds
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # How many tokens the LLM used — for cost tracking
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # RAGAS retrieval quality score between 0 and 1
    # Higher is better — used to detect degrading retrieval
    retrieval_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # How many times the self-healing agent retried
    # 0 means first retrieval was good enough
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Whether the response came from Redis cache
    was_cached: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    # Timestamp — indexed for time-range analytics queries
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<QueryLog org={self.org_id} latency={self.latency_ms}ms>"