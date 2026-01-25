"""Visit Information model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class VisitInfo(Base):
    """Visit information for the heritage site."""

    __tablename__ = "visit_info"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Basic info
    section: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # hours, tickets, transport, rules
    title: Mapped[str] = mapped_column(String(200))
    title_zh: Mapped[str] = mapped_column(String(200))

    # Content
    content: Mapped[str | None] = mapped_column(Text)
    content_zh: Mapped[str | None] = mapped_column(Text)

    # Additional data (JSON string for flexible content)
    extra_data: Mapped[str | None] = mapped_column(Text)  # JSON for opening hours, prices, etc.

    # Display order
    display_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
