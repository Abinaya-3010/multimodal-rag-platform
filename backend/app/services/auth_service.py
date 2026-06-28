import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.organization import Organization, DomainType, PlanType, OrgStatus
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


def register_organization(
    request: RegisterRequest,
    db: Session,
) -> TokenResponse:
    """
    Creates a new organization and its first admin user.

    Steps:
    1. Check the email and slug are not already taken
    2. Create the organization row
    3. Create the admin user row
    4. Generate and return tokens

    This all happens in one database transaction.
    If any step fails, nothing is saved — atomicity.
    """

    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == request.email
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Check if slug already exists
    existing_org = db.query(Organization).filter(
        Organization.slug == request.org_slug
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already taken",
        )

    # Generate a unique ID for the organization
    org_id = uuid.uuid4()

    # Derive the Qdrant collection name from org_id
    # This is the single source of truth for the collection name
    vector_collection = f"tenant_{str(org_id).replace('-', '')}_docs"

    # Derive the S3 prefix from org_id
    s3_prefix = f"tenants/{org_id}/"

    # Create the organization
    organization = Organization(
        id=org_id,
        name=request.org_name,
        slug=request.org_slug,
        vector_collection=vector_collection,
        s3_prefix=s3_prefix,
        domain_type=DomainType.other,
        plan=PlanType.free,
        status=OrgStatus.active,
        max_docs=100,
        is_active=True,
    )
    db.add(organization)

    # Create the first admin user
    user = User(
        id=uuid.uuid4(),
        org_id=org_id,
        email=request.email,
        hashed_password=hash_password(request.password),
        full_name=request.full_name,
        role=UserRole.org_admin,
        is_active=True,
    )
    db.add(user)

    # Commit both inserts in one transaction
    # If either fails, neither is saved
    db.commit()
    db.refresh(user)

    # Generate tokens with the user's identity embedded
    token_data = {
        "sub": str(user.id),
        "org_id": str(org_id),
        "role": user.role.value,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )


def login_user(
    request: LoginRequest,
    db: Session,
) -> TokenResponse:
    """
    Verifies credentials and returns tokens.

    Steps:
    1. Find the user by email
    2. Verify the password hash
    3. Check the user and org are active
    4. Generate and return tokens
    """

    # Find user by email
    user = db.query(User).filter(
        User.email == request.email
    ).first()

    # Use the same error message whether email or password is wrong
    # This prevents attackers from knowing which one failed
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
    )

    if not user:
        raise auth_error

    # Verify password against stored hash
    if not verify_password(request.password, user.hashed_password):
        raise auth_error

    # Check user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    # Check organization is active
    org = db.query(Organization).filter(
        Organization.id == user.org_id,
        Organization.is_active == True,
    ).first()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization is disabled",
        )

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "org_id": str(user.org_id),
        "role": user.role.value,
    }

    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
    )