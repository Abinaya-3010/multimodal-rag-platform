from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID


class RegisterRequest(BaseModel):
    """
    Data required to register a new organization.
    The first user becomes the org_admin automatically.
    """
    # Organization details
    org_name: str
    org_slug: str

    # First admin user details
    full_name: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_must_be_strong(cls, v: str) -> str:
        """
        Validate password strength before it ever reaches the database.
        Pydantic runs this automatically on every registration request.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("org_slug")
    @classmethod
    def slug_must_be_valid(cls, v: str) -> str:
        """
        Slugs must be URL-safe — only lowercase letters, numbers, hyphens.
        e.g. "apollo-hospital" not "Apollo Hospital"
        """
        import re
        if not re.match(r'^[a-z0-9-]+$', v):
            raise ValueError("Slug must contain only lowercase letters, numbers, and hyphens")
        return v


class LoginRequest(BaseModel):
    """
    Data required to log in.
    Email and password only — simple and secure.
    """
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """
    What the API returns after successful login or registration.
    The client stores both tokens.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """
    Data required to get a new access token.
    """
    refresh_token: str


class TokenPayload(BaseModel):
    """
    The data we embed inside the JWT token.
    Extracted by the auth middleware on every request.
    """
    sub: str        # user id
    org_id: str     # organization id
    role: str       # user role
    type: str       # "access" or "refresh"