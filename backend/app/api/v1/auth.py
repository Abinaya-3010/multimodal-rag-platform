from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse, MeResponse
from app.services.auth_service import register_organization, login_user
from app.core.deps import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization

# APIRouter groups related endpoints together
# prefix means all routes here start with /auth
# tags groups them in the /docs page
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """
    Register a new organization and its first admin user.
    Returns access and refresh tokens immediately.
    No email verification for now — can be added later.
    """
    return register_organization(request, db)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Login with email and password.
    Returns access and refresh tokens.
    """
    return login_user(request, db)


@router.get("/me", response_model=MeResponse)
def get_me(
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
):
    """
    Returns the current authenticated user's profile.
    This endpoint is protected — requires a valid JWT token.
    Used by the frontend to know who is logged in.
    """
    return MeResponse(
        user=UserResponse.model_validate(current_user),
        org_id=current_user.org_id,
        role=current_user.role,
    )