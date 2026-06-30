from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.core.deps import get_current_user, get_current_org
from app.models.user import User
from app.models.organization import Organization
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
)
from app.services.document_service import (
    upload_document,
    get_document_status,
    list_documents,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=202)
def upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Upload a document for processing.

    Returns immediately with status=pending (HTTP 202 Accepted).
    Processing happens asynchronously via Celery.
    Use GET /documents/{id}/status to poll for completion.
    """
    document = upload_document(
        file=file,
        org=current_org,
        user_id=current_user.id,
        db=db,
    )
    return DocumentUploadResponse(
        id=document.id,
        filename=document.filename,
        status=document.status,
    )


@router.get("", response_model=DocumentListResponse)
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    List all documents for the current organization.
    Paginated — defaults to 20 per page, max 100.
    """
    documents, total = list_documents(
        org_id=current_org.id,
        db=db,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
    )


@router.get("/{document_id}/status", response_model=DocumentResponse)
def get_status(
    document_id: UUID,
    current_org: Organization = Depends(get_current_org),
    db: Session = Depends(get_db),
):
    """
    Get the current processing status of a document.
    Frontend polls this endpoint after upload until status is "ready" or "failed".
    """
    document = get_document_status(
        document_id=document_id,
        org_id=current_org.id,
        db=db,
    )
    return DocumentResponse.model_validate(document)