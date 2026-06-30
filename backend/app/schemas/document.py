from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """
    What the API returns for a single document.
    Never expose s3_key directly — that's an internal detail.
    """
    id: UUID
    filename: str
    mime_type: str
    file_size_bytes: int
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    """
    Returned immediately after upload — before processing completes.
    The frontend uses the id to poll /documents/{id}/status.
    """
    id: UUID
    filename: str
    status: DocumentStatus
    message: str = "Document uploaded. Processing started."


class DocumentListResponse(BaseModel):
    """
    Paginated list of documents for the current tenant.
    """
    documents: list[DocumentResponse]
    total: int