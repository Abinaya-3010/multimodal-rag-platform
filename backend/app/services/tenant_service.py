import logging
from app.core.qdrant_client import (
    create_tenant_collection,
    delete_tenant_collection,
)
from app.core.s3_client import (
    ensure_bucket_exists,
    create_tenant_prefix,
    delete_tenant_prefix,
)

logger = logging.getLogger(__name__)


def provision_tenant_infrastructure(
    vector_collection: str,
    s3_prefix: str,
) -> None:
    """
    Creates the real infrastructure for a new tenant:
    1. A Qdrant collection
    2. An S3 prefix

    This follows the saga pattern:
    - If step 1 succeeds and step 2 fails,
      we roll back step 1 before raising the error.
    - This guarantees we never leave orphaned infrastructure.

    Called immediately after the organization row is created in PostgreSQL,
    inside the same registration flow.
    """

    # Track which steps succeeded so we know what to roll back
    qdrant_created = False

    try:
        # Step 1: Make sure the shared S3 bucket exists
        # This is idempotent — safe to call every time
        ensure_bucket_exists()

        # Step 2: Create the Qdrant collection
        create_tenant_collection(vector_collection)
        qdrant_created = True
        logger.info(f"Created Qdrant collection: {vector_collection}")

        # Step 3: Create the S3 prefix
        create_tenant_prefix(s3_prefix)
        logger.info(f"Created S3 prefix: {s3_prefix}")

    except Exception as e:
        logger.error(f"Tenant provisioning failed: {e}")

        # Roll back whatever succeeded before the failure
        if qdrant_created:
            try:
                delete_tenant_collection(vector_collection)
                logger.info(f"Rolled back Qdrant collection: {vector_collection}")
            except Exception as rollback_error:
                # Even rollback failures must be logged —
                # this becomes an orphaned resource requiring manual cleanup
                logger.error(f"Rollback failed for {vector_collection}: {rollback_error}")

        # Re-raise so the caller (registration endpoint) knows it failed
        # and can roll back the PostgreSQL transaction too
        raise


def deprovision_tenant_infrastructure(
    vector_collection: str,
    s3_prefix: str,
) -> None:
    """
    Permanently deletes a tenant's infrastructure.
    Used for GDPR right-to-erasure and tenant offboarding.
    This is irreversible — all vectors and files are gone.
    """
    delete_tenant_collection(vector_collection)
    delete_tenant_prefix(s3_prefix)
    logger.info(f"Deprovisioned tenant: {vector_collection}, {s3_prefix}")