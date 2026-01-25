"""Heritage site models."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HeritageCategory(Base):
    """Category for heritage sites (e.g., temples, historical buildings)."""

    __tablename__ = "heritage_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name_zh: Mapped[str] = mapped_column(String(100))  # Chinese name
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    sites: Mapped[list["HeritageSite"]] = relationship(back_populates="category")


class HeritageSite(Base):
    """Heritage site model representing a Taiwan historic site."""

    __tablename__ = "heritage_sites"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    name_zh: Mapped[str] = mapped_column(String(200), index=True)  # Chinese name
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    # Location
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    latitude: Mapped[float | None] = mapped_column()
    longitude: Mapped[float | None] = mapped_column()

    # Content
    description: Mapped[str | None] = mapped_column(Text)
    description_zh: Mapped[str | None] = mapped_column(Text)
    history: Mapped[str | None] = mapped_column(Text)
    history_zh: Mapped[str | None] = mapped_column(Text)

    # Media
    featured_image: Mapped[str | None] = mapped_column(String(500))
    images: Mapped[str | None] = mapped_column(Text)  # JSON array of image URLs

    # Metadata
    designation_level: Mapped[str | None] = mapped_column(String(100))  # National, Municipal, etc.
    designation_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_published: Mapped[bool] = mapped_column(default=False)

    # Category relationship
    category_id: Mapped[int | None] = mapped_column(ForeignKey("heritage_categories.id"))
    category: Mapped[HeritageCategory | None] = relationship(back_populates="sites")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
