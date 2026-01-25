"""File upload API endpoints using pre-signed URLs."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUserFromCookie
from app.core.s3 import generate_presigned_upload_url, get_allowed_types_info
from app.schemas.upload import (
    AllowedTypesResponse,
    MultiPresignedUrlRequest,
    MultiPresignedUrlResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
)

router = APIRouter()

MAX_MULTIPLE_FILES = 10


@router.post("/presign", response_model=PresignedUrlResponse)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    _: CurrentUserFromCookie,
) -> PresignedUrlResponse:
    """Get a pre-signed URL for uploading a single file to S3.

    Requires authentication.

    The client should use the returned `upload_url` to PUT the file directly to S3.
    After successful upload, the file will be accessible at `public_url`.

    Allowed file types:
    - Images: jpg, png, webp, gif (max 10 MB)
    - Videos: mp4, webm, mov (max 100 MB)
    """
    try:
        result = await generate_presigned_upload_url(
            filename=request.filename,
            content_type=request.content_type,
        )
        return PresignedUrlResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/presign/multiple", response_model=MultiPresignedUrlResponse)
async def get_presigned_upload_urls(
    request: MultiPresignedUrlRequest,
    _: CurrentUserFromCookie,
) -> MultiPresignedUrlResponse:
    """Get pre-signed URLs for uploading multiple files to S3 (max 10 files).

    Requires authentication.

    Allowed file types:
    - Images: jpg, png, webp, gif (max 10 MB each)
    - Videos: mp4, webm, mov (max 100 MB each)
    """
    if len(request.files) > MAX_MULTIPLE_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_MULTIPLE_FILES} files allowed per request",
        )

    urls: list[PresignedUrlResponse] = []

    for file_req in request.files:
        try:
            result = await generate_presigned_upload_url(
                filename=file_req.filename,
                content_type=file_req.content_type,
            )
            urls.append(PresignedUrlResponse(**result))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error for '{file_req.filename}': {e}",
            )

    return MultiPresignedUrlResponse(
        urls=urls,
        total_count=len(urls),
    )


@router.get("/allowed-types", response_model=AllowedTypesResponse)
async def get_allowed_types() -> AllowedTypesResponse:
    """Get allowed file types and size limits.

    This endpoint does not require authentication.
    """
    info = get_allowed_types_info()
    return AllowedTypesResponse(**info)
