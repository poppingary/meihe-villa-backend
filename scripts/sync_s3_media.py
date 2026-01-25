#!/usr/bin/env python3
"""Sync existing S3 media files to the database.

This script scans the S3 bucket and creates MediaFile records
for any files that don't already exist in the database.

Usage:
    python scripts/sync_s3_media.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import boto3
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.media import MediaFile

settings = get_settings()


def get_content_type(key: str) -> str:
    """Determine content type from file extension."""
    ext = key.lower().split(".")[-1]
    types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
    }
    return types.get(ext, "application/octet-stream")


def get_category(content_type: str) -> str:
    """Determine category from content type."""
    if content_type.startswith("image/"):
        return "images"
    elif content_type.startswith("video/"):
        return "videos"
    return "other"


async def sync_s3_to_db():
    """Scan S3 bucket and create missing MediaFile records."""
    s3 = boto3.client(
        "s3",
        region_name=settings.aws_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )

    bucket = settings.s3_bucket_name
    cloudfront_domain = settings.cloudfront_domain

    # List all objects in bucket
    paginator = s3.get_paginator("list_objects_v2")
    all_objects = []
    for page in paginator.paginate(Bucket=bucket):
        all_objects.extend(page.get("Contents", []))

    print(f"Found {len(all_objects)} files in S3 bucket '{bucket}'")

    async with AsyncSessionLocal() as db:
        created = 0
        skipped = 0

        for obj in all_objects:
            key = obj["Key"]

            # Skip if already exists in database
            query = select(MediaFile).where(MediaFile.s3_key == key)
            result = await db.execute(query)
            if result.scalar_one_or_none():
                skipped += 1
                continue

            content_type = get_content_type(key)
            category = get_category(content_type)
            filename = key.split("/")[-1]
            folder = "/".join(key.split("/")[:-1]) if "/" in key else None

            # Build public URL
            if cloudfront_domain:
                public_url = f"https://{cloudfront_domain}/{key}"
            else:
                public_url = f"https://{bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"

            media = MediaFile(
                filename=filename,
                original_filename=filename,
                s3_key=key,
                public_url=public_url,
                content_type=content_type,
                file_size=obj.get("Size"),
                category=category,
                folder=folder,
            )
            db.add(media)
            created += 1
            print(f"  + {key}")

        await db.commit()
        print(f"\nCreated {created} new records, skipped {skipped} existing")


if __name__ == "__main__":
    asyncio.run(sync_s3_to_db())
