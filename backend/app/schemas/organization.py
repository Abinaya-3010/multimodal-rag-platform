from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.organization import DomainType, PlanType, OrgStatus


class OrganizationResponse(BaseModel):
    """
    What the API returns when showing organization data.
    Never expose internal fields like s3_prefix or vector_collection.
    """
    id: UUID
    name: str
    slug: str
    domain_type: DomainType
    plan: PlanType
    status: OrgStatus
    max_docs: int
    is_active: bool
    created_at: datetime

    # This tells Pydantic to read data from SQLAlchemy model attributes
    # Without this, Pydantic cannot read SQLAlchemy objects
    model_config = {"from_attributes": True}