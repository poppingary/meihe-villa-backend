"""Media files model for tracking uploaded files."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MediaFile(Base):
    """Media file metadata for uploaded images and videos."""

    __tablename__ = "media_files"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # File info
    filename: Mapped[str] = mapped_column(String(255))
    original_filename: Mapped[str] = mapped_column(String(255))
    s3_key: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    public_url: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int | None] = mapped_column(Integer)

    # Categorization
    category: Mapped[str] = mapped_column(String(50), index=True)  # images, videos
    folder: Mapped[str | None] = mapped_column(String(100), index=True)  # custom folder

    # Metadata
    alt_text: Mapped[str | None] = mapped_column(String(255))
    alt_text_zh: Mapped[str | None] = mapped_column(String(255))
    caption: Mapped[str | None] = mapped_column(Text)
    caption_zh: Mapped[str | None] = mapped_column(Text)

    # Image dimensions (for images only)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
