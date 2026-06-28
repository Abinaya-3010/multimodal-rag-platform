# This file imports all models so Alembic can find them
# when generating migrations
from app.models.organization import Organization
from app.models.user import User
from app.models.document import Document
from app.models.query_log import QueryLog