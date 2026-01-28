"""Media files API endpoints."""

import logging
import math

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUserFromCookie, DbSession
from app.core.s3 import delete_s3_object, get_public_url, rename_s3_object
from app.models.media import MediaFile
from app.schemas.media import (
    MediaFileCreate,
    MediaFileListResponse,
    MediaFileResponse,
    MediaFileUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=MediaFileListResponse)
async def list_media_files(
    db: DbSession,
    _: CurrentUserFromCookie,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    folder: str | None = None,
    search: str | None = None,
):
    """List media files with pagination and filtering."""
    query = select(MediaFile)

    # Apply filters
    if category:
        query = query.where(MediaFile.category == category)
    if folder:
        query = query.where(MediaFile.folder == folder)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            MediaFile.original_filename.ilike(search_term)
            | MediaFile.alt_text.ilike(search_term)
            | MediaFile.alt_text_zh.ilike(search_term)
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Pagination
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Get items
    query = query.order_by(MediaFile.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return MediaFileListResponse(
        items=[MediaFileResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media_file(
    db: DbSession,
    _: CurrentUserFromCookie,
    media_id: int,
):
    """Get a single media file by ID."""
    query = select(MediaFile).where(MediaFile.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    return media


@router.post("", response_model=MediaFileResponse, status_code=status.HTTP_201_CREATED)
async def create_media_file(
    db: DbSession,
    _: CurrentUserFromCookie,
    media_in: MediaFileCreate,
):
    """Create a new media file record after successful upload."""
    media = MediaFile(**media_in.model_dump())
    db.add(media)
    await db.flush()
    await db.refresh(media)
    return media


@router.patch("/{media_id}", response_model=MediaFileResponse)
async def update_media_file(
    db: DbSession,
    _: CurrentUserFromCookie,
    media_id: int,
    media_in: MediaFileUpdate,
):
    """Update media file metadata."""
    query = select(MediaFile).where(MediaFile.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    update_data = media_in.model_dump(exclude_unset=True)

    # Handle rename: update S3 key, public_url, filename, original_filename
    if "original_filename" in update_data and update_data["original_filename"]:
        new_filename = update_data["original_filename"]
        # Make filename safe
        safe_filename = new_filename.replace(" ", "-")

        new_key = await rename_s3_object(media.s3_key, safe_filename)
        if new_key is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to rename file in storage",
            )

        media.s3_key = new_key
        media.public_url = get_public_url(new_key)
        media.filename = safe_filename
        media.original_filename = new_filename
        # Remove from update_data so it's not set again
        del update_data["original_filename"]

    for field, value in update_data.items():
        setattr(media, field, value)

    await db.flush()
    await db.refresh(media)
    return media


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_file(
    db: DbSession,
    _: CurrentUserFromCookie,
    media_id: int,
):
    """Delete a media file record and its S3 object."""
    query = select(MediaFile).where(MediaFile.id == media_id)
    result = await db.execute(query)
    media = result.scalar_one_or_none()

    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found",
        )

    # Delete from S3
    if media.s3_key:
        s3_deleted = await delete_s3_object(media.s3_key)
        if not s3_deleted:
            logger.warning(f"Failed to delete S3 object: {media.s3_key}")

    # Delete from database
    await db.delete(media)


@router.delete("/by-url/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media_by_url(
    db: DbSession,
    _: CurrentUserFromCookie,
    url: str,
):
    """Delete a media file by its public URL.

    This endpoint is useful when you only have the URL (e.g., from a form field)
    and need to delete the corresponding media file and S3 object.
    """
    query = select(MediaFile).where(MediaFile.public_url == url)
    result = await db.execute(query)
    media = result.scalar_one_or_none()

    if not media:
        # Media record not found - this could be an external URL or already deleted
        # Just return success since the goal is to remove the file
        return

    # Delete from S3
    if media.s3_key:
        s3_deleted = await delete_s3_object(media.s3_key)
        if not s3_deleted:
            logger.warning(f"Failed to delete S3 object: {media.s3_key}")

    # Delete from database
    await db.delete(media)


@router.get("/folders/list", response_model=list[str])
async def list_folders(
    db: DbSession,
    _: CurrentUserFromCookie,
):
    """Get list of unique folders."""
    query = (
        select(MediaFile.folder)
        .where(MediaFile.folder.isnot(None))
        .distinct()
        .order_by(MediaFile.folder)
    )
    result = await db.execute(query)
    folders = [row[0] for row in result.all() if row[0]]
    return folders
