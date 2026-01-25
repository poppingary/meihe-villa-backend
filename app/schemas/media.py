"""Pydantic schemas for media files."""

from datetime import datetime

from pydantic import BaseModel


class MediaFileBase(BaseModel):
    """Base schema for media files."""

    alt_text: str | None = None
    alt_text_zh: str | None = None
    caption: str | None = None
    caption_zh: str | None = None
    folder: str | None = None


class MediaFileCreate(MediaFileBase):
    """Schema for creating a media file record after upload."""

    filename: str
    original_filename: str
    s3_key: str
    public_url: str
    content_type: str
    file_size: int | None = None
    category: str
    width: int | None = None
    height: int | None = None


class MediaFileUpdate(MediaFileBase):
    """Schema for updating media file metadata."""

    pass


class MediaFileResponse(MediaFileBase):
    """Schema for media file response."""

    id: int
    filename: str
    original_filename: str
    s3_key: str
    public_url: str
    content_type: str
    file_size: int | None
    category: str
    width: int | None
    height: int | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MediaFileListResponse(BaseModel):
    """Schema for paginated media file list."""

    items: list[MediaFileResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
