import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
import enum


class DomainType(str, enum.Enum):
    hospital = "hospital"
    legal = "legal"
    enterprise = "enterprise"
    university = "university"
    manufacturing = "manufacturing"
    finance = "finance"
    hr = "hr"
    other = "other"


class PlanType(str, enum.Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class OrgStatus(str, enum.Enum):
    provisioning = "provisioning"
    active = "active"
    suspended = "suspended"
    deleting = "deleting"


class Organization(Base):
    __tablename__ = "organizations"

    # Primary key — UUID instead of integer
    # UUID means no sequential ID guessing attacks
    # e.g. attacker cannot try /orgs/1, /orgs/2, /orgs/3
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Display name shown in the UI
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # URL-safe short identifier e.g. "apollo-hospital"
    # unique=True means no two orgs can have the same slug
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    # Exact Qdrant collection name for this tenant
    # Stored here so we never recompute it — single source of truth
    vector_collection: Mapped[str] = mapped_column(String(200), nullable=False)

    # S3 path prefix e.g. "tenants/abc123/"
    s3_prefix: Mapped[str] = mapped_column(String(200), nullable=False)

    # What kind of organization this is
    domain_type: Mapped[DomainType] = mapped_column(
        SAEnum(DomainType),
        nullable=False,
        default=DomainType.other,
    )

    # Subscription plan
    plan: Mapped[PlanType] = mapped_column(
        SAEnum(PlanType),
        nullable=False,
        default=PlanType.free,
    )

    # Lifecycle status
    status: Mapped[OrgStatus] = mapped_column(
        SAEnum(OrgStatus),
        nullable=False,
        default=OrgStatus.provisioning,
    )

    # Maximum documents allowed — enforced at upload time
    max_docs: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    # Soft disable without deleting data
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Audit timestamps — always know when a record was created or changed
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

    def __repr__(self) -> str:
        return f"<Organization {self.name} ({self.slug})>"