"""Historical Timeline model."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimelineEvent(Base):
    """Historical timeline events for the heritage site."""

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Date information
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int | None] = mapped_column(Integer)
    day: Mapped[int | None] = mapped_column(Integer)
    era: Mapped[str | None] = mapped_column(String(50))  # e.g., "清同治", "日治", "民國"
    era_year: Mapped[str | None] = mapped_column(String(50))  # e.g., "同治8年", "大正12年"

    # Content
    title: Mapped[str] = mapped_column(String(200))
    title_zh: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    description_zh: Mapped[str | None] = mapped_column(Text)

    # Media
    image: Mapped[str | None] = mapped_column(String(500))

    # Categorization
    category: Mapped[str | None] = mapped_column(String(50))  # construction, restoration, cultural, political
    importance: Mapped[str | None] = mapped_column(String(20), default="normal")  # major, normal, minor

    # Display
    is_published: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
