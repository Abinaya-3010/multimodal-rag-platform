import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status, UploadFile

from app.models.document import Document, DocumentStatus
from app.models.organization import Organization
from app.core.s3_client import s3
from app.core.config import get_settings

settings = get_settings()

# Allowed file types — anything else is rejected before it touches storage
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "text/html",
    "text/csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "image/png",
    "image/jpeg",
}

# 50 MB limit per file — generous enough for most documents,
# small enough to prevent abuse
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


def upload_document(
    file: UploadFile,
    org: Organization,
    user_id: uuid.UUID,
    db: Session,
) -> Document:
    """
    Handles the full upload flow:
    1. Validate file type and size
    2. Check tenant's document limit
    3. Upload raw bytes to S3
    4. Create the database row
    5. Dispatch the Celery task

    Returns the Document object with status=pending.
    The actual processing happens asynchronously.
    """

    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{file.content_type}' is not supported",
        )

    # Read the file into memory to check size
    # For very large files in production, we would stream this instead
    file_bytes = file.file.read()
    file_size = len(file_bytes)

    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)}MB",
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is empty",
        )

    # Check tenant's document count against their plan limit
    current_doc_count = db.query(func.count(Document.id)).filter(
        Document.org_id == org.id
    ).scalar()

    if current_doc_count >= org.max_docs:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Document limit reached ({org.max_docs}). Upgrade your plan to upload more.",
        )

    # Generate a unique ID for this document
    doc_id = uuid.uuid4()

    # Build the S3 key — this is where tenant isolation happens for files
    # Format: tenants/{org_id}/raw/{doc_id}/{filename}
    s3_key = f"{org.s3_prefix}raw/{doc_id}/{file.filename}"

    # Upload to S3
    try:
        s3.put_object(
            Bucket=settings.s3_bucket_name,
            Key=s3_key,
            Body=file_bytes,
            ContentType=file.content_type,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}",
        )

    # Create the database row
    document = Document(
        id=doc_id,
        org_id=org.id,
        uploaded_by=user_id,
        filename=file.filename,
        s3_key=s3_key,
        mime_type=file.content_type,
        file_size_bytes=file_size,
        status=DocumentStatus.pending,
        chunk_count=0,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Dispatch the Celery task
    # .delay() is shorthand for sending the task to the queue
    # The worker process picks it up independently
    from app.workers.ingestion_tasks import process_document_task
    process_document_task.delay(str(doc_id), str(org.id))

    return document


def get_document_status(
    document_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Session,
) -> Document:
    """
    Fetches a single document, scoped to the requesting org.
    The org_id filter here is critical — without it, any authenticated
    user could query any document by guessing UUIDs.
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.org_id == org_id,
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


def list_documents(
    org_id: uuid.UUID,
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Document], int]:
    """
    Returns a paginated list of documents for the org.
    Always filtered by org_id — this IS the tenant isolation enforcement
    at the application layer, backed by the database design.
    """
    query = db.query(Document).filter(Document.org_id == org_id)

    total = query.count()
    documents = (
        query.order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return documents, total