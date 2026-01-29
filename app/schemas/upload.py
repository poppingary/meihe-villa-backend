"""Pydantic schemas for file uploads."""

from pydantic import BaseModel


class PresignedUrlRequest(BaseModel):
    """Request schema for generating a pre-signed upload URL."""

    filename: str
    content_type: str
    folder: str | None = None


class PresignedUrlResponse(BaseModel):
    """Response schema for a pre-signed upload URL."""

    upload_url: str
    public_url: str
    s3_key: str
    content_type: str
    max_size: int
    expires_in: int


class MultiPresignedUrlRequest(BaseModel):
    """Request schema for generating multiple pre-signed upload URLs."""

    files: list[PresignedUrlRequest]


class MultiPresignedUrlResponse(BaseModel):
    """Response schema for multiple pre-signed upload URLs."""

    urls: list[PresignedUrlResponse]
    total_count: int


class FileTypeInfo(BaseModel):
    """Information about allowed file types."""

    types: list[str]
    extensions: list[str]
    max_size_bytes: int
    max_size_mb: float


class AllowedTypesResponse(BaseModel):
    """Response schema for allowed file types endpoint."""

    images: FileTypeInfo
    videos: FileTypeInfo
