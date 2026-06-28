import hashlib
from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import get_settings

settings = get_settings()

# CryptContext tells passlib to use bcrypt for hashing
# bcrypt automatically salts passwords — each hash is unique
# even if two users have the same password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Takes a plain text password and returns a bcrypt hash.
    The hash looks like: $2b$12$... and is safe to store in the database.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain text password against a stored hash.
    Returns True if they match, False otherwise.
    Never compares plain text to plain text.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict[str, Any]) -> str:
    """
    Creates a JWT access token.
    The token contains the user's id, org_id, and role.
    It expires after JWT_ACCESS_TOKEN_EXPIRE_MINUTES minutes.
    It is signed with JWT_SECRET_KEY so it cannot be forged.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    """
    Creates a JWT refresh token with a longer expiry.
    Used to get new access tokens without re-logging in.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decodes and verifies a JWT token.
    Raises JWTError if the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def hash_string(value: str) -> str:
    """
    Creates a SHA-256 hash of any string.
    Used for hashing query text before storing in query_logs
    and for Redis cache keys.
    """
    return hashlib.sha256(value.encode()).hexdigest()