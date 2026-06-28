from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

# Create the SQLAlchemy engine
# The engine is the connection to PostgreSQL
# pool_pre_ping=True tests the connection before using it
# This prevents errors from stale connections
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# SessionLocal is a factory that creates database sessions
# Each request gets its own session
# autocommit=False means we control when to save changes
# autoflush=False means SQLAlchemy waits for us to flush
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Base class for all SQLAlchemy models
# Every model we create will inherit from this
class Base(DeclarativeBase):
    pass


def get_db():
    """
    Dependency function for FastAPI.
    Creates a database session for each request,
    then closes it when the request is done.
    The try/finally ensures the session always closes,
    even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()