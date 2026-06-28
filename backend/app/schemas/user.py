from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole


class UserResponse(BaseModel):
    """
    What the API returns when showing user data.
    Never expose hashed_password in any response.
    """
    id: UUID
    org_id: UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    """
    Response for the /auth/me endpoint.
    Returns both user and organization info in one call.
    """
    user: UserResponse
    org_id: UUID
    role: UserRole
    