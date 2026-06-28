from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError
from uuid import UUID

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.models.organization import Organization

# HTTPBearer extracts the token from the Authorization header
# It looks for "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency that protects any route.
    Add this to any endpoint to require authentication.

    FastAPI automatically:
    1. Extracts the Bearer token from the Authorization header
    2. Calls this function
    3. Injects the verified User object into your endpoint

    If the token is missing, invalid, or expired,
    FastAPI returns 401 automatically before your code runs.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and verify the JWT signature
        payload = decode_token(credentials.credentials)

        # Extract user id from the token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Make sure this is an access token, not a refresh token
        token_type: str = payload.get("type")
        if token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Look up the user in the database
    # We verify the user still exists and is still active
    user = db.query(User).filter(
        User.id == UUID(user_id),
        User.is_active == True,
    ).first()

    if user is None:
        raise credentials_exception

    return user


def get_current_org(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Organization:
    """
    Dependency that returns the current user's organization.
    Use this when you need both the user and their org.
    """
    org = db.query(Organization).filter(
        Organization.id == current_user.org_id,
        Organization.is_active == True,
    ).first()

    if org is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return org


def require_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that requires the user to be an org_admin.
    Use this on endpoints that only admins can access
    like inviting members or deleting documents.
    """
    if current_user.role != "org_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user