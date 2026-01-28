"""AWS S3 service for pre-signed URL generation."""

import uuid
from datetime import datetime

import aioboto3

from app.config import get_settings

# Allowed content types and their categories
ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
}

# File size limits in bytes
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100 MB


def get_file_category(content_type: str) -> str | None:
    """Get file category (images/videos) based on content type."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return "images"
    if content_type in ALLOWED_VIDEO_TYPES:
        return "videos"
    return None


def get_max_size_for_type(content_type: str) -> int:
    """Get maximum file size based on content type."""
    if content_type in ALLOWED_IMAGE_TYPES:
        return MAX_IMAGE_SIZE
    if content_type in ALLOWED_VIDEO_TYPES:
        return MAX_VIDEO_SIZE
    return 0


def validate_content_type(content_type: str) -> bool:
    """Check if content type is allowed."""
    return content_type in ALLOWED_IMAGE_TYPES or content_type in ALLOWED_VIDEO_TYPES


def generate_s3_key(filename: str, content_type: str) -> str:
    """Generate a unique S3 key with date-based folder structure."""
    category = get_file_category(content_type)
    if not category:
        raise ValueError(f"Unsupported content type: {content_type}")

    now = datetime.utcnow()
    unique_id = uuid.uuid4().hex[:8]
    safe_filename = filename.replace(" ", "-")

    return f"{category}/{now.year}/{now.month:02d}/{unique_id}-{safe_filename}"


def get_public_url(s3_key: str) -> str:
    """Get the public URL for an S3 object (via CloudFront or direct S3)."""
    settings = get_settings()

    if settings.cloudfront_domain:
        return f"https://{settings.cloudfront_domain}/{s3_key}"
    return (
        f"https://{settings.s3_bucket_name}.s3."
        f"{settings.aws_region}.amazonaws.com/{s3_key}"
    )


async def generate_presigned_upload_url(
    filename: str,
    content_type: str,
) -> dict:
    """Generate a pre-signed URL for uploading a file to S3.

    Returns:
        dict with upload_url, public_url, s3_key, content_type, max_size, expires_in
    """
    settings = get_settings()

    # Validate content type
    if not validate_content_type(content_type):
        allowed = list(ALLOWED_IMAGE_TYPES.keys()) + list(ALLOWED_VIDEO_TYPES.keys())
        raise ValueError(
            f"Content type '{content_type}' not allowed. Allowed: {allowed}"
        )

    # Generate S3 key
    s3_key = generate_s3_key(filename, content_type)
    max_size = get_max_size_for_type(content_type)

    # Create S3 session
    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )

    # Generate pre-signed URL
    async with session.client("s3") as s3:
        upload_url = await s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": s3_key,
                "ContentType": content_type,
            },
            ExpiresIn=settings.presigned_url_expiration,
        )

    return {
        "upload_url": upload_url,
        "public_url": get_public_url(s3_key),
        "s3_key": s3_key,
        "content_type": content_type,
        "max_size": max_size,
        "expires_in": settings.presigned_url_expiration,
    }


async def generate_presigned_download_url(s3_key: str) -> str:
    """Generate a pre-signed URL for downloading a private S3 object."""
    settings = get_settings()

    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )

    async with session.client("s3") as s3:
        url = await s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": settings.s3_bucket_name,
                "Key": s3_key,
            },
            ExpiresIn=settings.presigned_url_expiration,
        )

    return url


async def copy_s3_object(old_key: str, new_key: str) -> bool:
    """Copy an S3 object to a new key.

    Args:
        old_key: The current S3 key
        new_key: The destination S3 key

    Returns:
        True if copy was successful, False otherwise
    """
    settings = get_settings()

    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )

    try:
        async with session.client("s3") as s3:
            await s3.copy_object(
                Bucket=settings.s3_bucket_name,
                CopySource=f"{settings.s3_bucket_name}/{old_key}",
                Key=new_key,
            )
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to copy S3 object {old_key} -> {new_key}: {e}")
        return False


async def rename_s3_object(old_key: str, new_filename: str) -> str | None:
    """Rename an S3 object by copying to a new key and deleting the old one.

    Args:
        old_key: The current S3 key
        new_filename: The new filename (just the name, not the full path)

    Returns:
        The new S3 key if successful, None otherwise
    """
    # Build new key: same prefix path, new filename
    parts = old_key.rsplit("/", 1)
    if len(parts) == 2:
        prefix = parts[0]
        new_key = f"{prefix}/{new_filename}"
    else:
        new_key = new_filename

    if new_key == old_key:
        return old_key

    copied = await copy_s3_object(old_key, new_key)
    if not copied:
        return None

    await delete_s3_object(old_key)
    return new_key


async def delete_s3_object(s3_key: str) -> bool:
    """Delete an object from S3.

    Args:
        s3_key: The S3 key of the object to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    settings = get_settings()

    session = aioboto3.Session(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )

    try:
        async with session.client("s3") as s3:
            await s3.delete_object(
                Bucket=settings.s3_bucket_name,
                Key=s3_key,
            )
        return True
    except Exception:
        return False


def get_allowed_types_info() -> dict:
    """Get information about allowed file types and size limits."""
    return {
        "images": {
            "types": list(ALLOWED_IMAGE_TYPES.keys()),
            "extensions": list(ALLOWED_IMAGE_TYPES.values()),
            "max_size_bytes": MAX_IMAGE_SIZE,
            "max_size_mb": MAX_IMAGE_SIZE / (1024 * 1024),
        },
        "videos": {
            "types": list(ALLOWED_VIDEO_TYPES.keys()),
            "extensions": list(ALLOWED_VIDEO_TYPES.values()),
            "max_size_bytes": MAX_VIDEO_SIZE,
            "max_size_mb": MAX_VIDEO_SIZE / (1024 * 1024),
        },
    }
