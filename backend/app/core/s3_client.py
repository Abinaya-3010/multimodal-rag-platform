import boto3
from botocore.exceptions import ClientError
from app.core.config import get_settings

settings = get_settings()

# Single shared S3 client
# Works identically against MinIO (local) and AWS S3 (production)
# Only the endpoint_url changes between environments
s3 = boto3.client(
    "s3",
    endpoint_url=settings.minio_endpoint,
    aws_access_key_id=settings.aws_access_key_id,
    aws_secret_access_key=settings.aws_secret_access_key,
)


def ensure_bucket_exists() -> None:
    """
    Creates the shared bucket if it doesn't exist yet.
    We use ONE bucket for the whole platform, with tenant
    isolation done through key prefixes, not separate buckets.
    This is simpler to manage than one bucket per tenant.
    """
    try:
        s3.head_bucket(Bucket=settings.s3_bucket_name)
    except ClientError:
        # Bucket doesn't exist — create it
        s3.create_bucket(Bucket=settings.s3_bucket_name)


def create_tenant_prefix(s3_prefix: str) -> None:
    """
    S3 doesn't have real folders — prefixes are just part of the key name.
    We create a placeholder object so the prefix is visible
    in tools like the MinIO console, and so we can verify
    provisioning succeeded.
    """
    s3.put_object(
        Bucket=settings.s3_bucket_name,
        Key=f"{s3_prefix}.init",
        Body=b"",
    )


def delete_tenant_prefix(s3_prefix: str) -> None:
    """
    Deletes every object under a tenant's prefix.
    Used for rollback and tenant offboarding.
    """
    response = s3.list_objects_v2(
        Bucket=settings.s3_bucket_name,
        Prefix=s3_prefix,
    )
    objects = response.get("Contents", [])
    if objects:
        s3.delete_objects(
            Bucket=settings.s3_bucket_name,
            Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
        )


def prefix_exists(s3_prefix: str) -> bool:
    """
    Checks if a tenant's prefix has been created.
    """
    response = s3.list_objects_v2(
        Bucket=settings.s3_bucket_name,
        Prefix=s3_prefix,
        MaxKeys=1,
    )
    return response.get("KeyCount", 0) > 0