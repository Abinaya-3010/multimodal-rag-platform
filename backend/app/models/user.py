import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
import enum


class UserRole(str, enum.Enum):
    org_admin = "org_admin"
    member = "member"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Foreign key to organizations table
    # ondelete="CASCADE" means if the org is deleted,
    # all its users are automatically deleted too
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        # index=True creates a database index on this column
        # This makes queries like "find all users in org X" very fast
    )

    # Login identifier — must be unique across the entire platform
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # bcrypt hash of the password — never store plain text passwords
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Full name for display
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Role within the organization
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole),
        nullable=False,
        default=UserRole.member,
    )

    # Account state
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Track last login for security auditing
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
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

    # Relationship — lets you do user.organization to get the org object
    # back_populates connects to Organization.users if we add that later
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"