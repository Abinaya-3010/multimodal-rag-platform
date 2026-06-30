import logging
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: str, org_id: str):
    """
    Placeholder ingestion task.

    bind=True gives us access to "self" — the task instance —
    which lets us retry, update state, and inspect retry count.

    max_retries=3 means if this task raises an exception,
    Celery will automatically retry it up to 3 times
    with exponential backoff, before giving up.

    The REAL parsing/chunking/embedding logic gets built in Module 6.
    For now, this just proves the full async pipeline works:
    upload -> dispatch -> worker picks it up -> updates status.
    """
    logger.info(f"Processing document {document_id} for org {org_id}")

    # In Module 6, this is where we will:
    # 1. Download the file from S3
    # 2. Parse it with Unstructured.io
    # 3. Run OCR if needed
    # 4. Chunk the text
    # 5. Generate embeddings
    # 6. Upsert into the tenant's Qdrant collection
    # 7. Update the document status to "ready"

    # For now, just simulate success
    from app.db.session import SessionLocal
    from app.models.document import Document, DocumentStatus
    import uuid

    db = SessionLocal()
    try:
        document = db.query(Document).filter(
            Document.id == uuid.UUID(document_id)
        ).first()

        if document:
            document.status = DocumentStatus.ready
            document.chunk_count = 0  # will be real once Module 6 is built
            db.commit()
            logger.info(f"Document {document_id} marked as ready (placeholder)")
        else:
            logger.error(f"Document {document_id} not found")

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        db.rollback()
        raise
    finally:
        db.close()