#!/usr/bin/env python3
"""Seed database with initial data.

Usage:
    # Seed all data (upsert mode - updates existing, inserts new)
    uv run python scripts/seed_db.py

    # Seed specific tables only
    uv run python scripts/seed_db.py --tables categories,sites,visit_info

    # Reset and reseed (WARNING: deletes existing data first)
    uv run python scripts/seed_db.py --reset

    # Dry run (show what would be done without making changes)
    uv run python scripts/seed_db.py --dry-run
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.heritage import HeritageCategory, HeritageSite
from app.models.media import MediaFile
from app.models.news import News
from app.models.timeline import TimelineEvent
from app.models.visit_info import VisitInfo

# Load seed data
SEED_DATA_PATH = Path(__file__).parent / "seed_data.json"


# =============================================================================
# Pydantic Models for Seed Data Validation
# =============================================================================


class CategorySeed(BaseModel):
    """Schema for heritage category seed data."""

    name: str
    name_zh: str
    description: str | None = None


class SiteSeed(BaseModel):
    """Schema for heritage site seed data."""

    name: str
    name_zh: str
    slug: str
    address: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    description_zh: str | None = None
    history: str | None = None
    history_zh: str | None = None
    featured_image: str | None = None
    images: str | None = None
    designation_level: str | None = None
    designation_date: str | None = None
    is_published: bool = False
    category_name: str | None = None


class VisitInfoSeed(BaseModel):
    """Schema for visit info seed data."""

    section: str
    title: str
    title_zh: str
    content: str | None = None
    content_zh: str | None = None
    extra_data: str | None = None
    display_order: int = 0
    is_active: bool = True

    @field_validator("extra_data")
    @classmethod
    def validate_extra_data_json(cls, v: str | None) -> str | None:
        """Validate that extra_data is valid JSON if provided."""
        if v is None:
            return v
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"extra_data must be valid JSON: {e}")


class TimelineEventSeed(BaseModel):
    """Schema for timeline event seed data."""

    year: int
    month: int | None = None
    day: int | None = None
    era: str | None = None
    era_year: str | None = None
    title: str
    title_zh: str
    description: str | None = None
    description_zh: str | None = None
    image: str | None = None
    category: str | None = None
    importance: str = "normal"
    is_published: bool = True


class NewsSeed(BaseModel):
    """Schema for news seed data."""

    title: str
    title_zh: str
    slug: str
    summary: str | None = None
    summary_zh: str | None = None
    content: str | None = None
    content_zh: str | None = None
    featured_image: str | None = None
    images: str | None = None
    category: str | None = None
    is_published: bool = False
    published_at: str | None = None


class MediaFileSeed(BaseModel):
    """Schema for media file seed data."""

    filename: str
    original_filename: str
    s3_key: str
    public_url: str
    content_type: str
    file_size: int | None = None
    category: str
    folder: str | None = None
    alt_text: str | None = None
    alt_text_zh: str | None = None
    caption: str | None = None
    caption_zh: str | None = None
    width: int | None = None
    height: int | None = None


class SeedData(BaseModel):
    """Schema for complete seed data file."""

    heritage_categories: list[CategorySeed] = Field(default_factory=list)
    heritage_sites: list[SiteSeed] = Field(default_factory=list)
    visit_info: list[VisitInfoSeed] = Field(default_factory=list)
    timeline_events: list[TimelineEventSeed] = Field(default_factory=list)
    news: list[NewsSeed] = Field(default_factory=list)
    media_files: list[MediaFileSeed] = Field(default_factory=list)


# =============================================================================
# Data Loading
# =============================================================================


def load_seed_data() -> SeedData:
    """Load and validate seed data from JSON file.

    Returns:
        SeedData: Validated seed data object.

    Raises:
        FileNotFoundError: If seed data file doesn't exist.
        ValidationError: If seed data doesn't match expected schema.
        json.JSONDecodeError: If seed data file contains invalid JSON.
    """
    with open(SEED_DATA_PATH) as f:
        raw_data = json.load(f)

    return SeedData.model_validate(raw_data)


# =============================================================================
# Seeder Functions
# =============================================================================


async def seed_categories(
    db: AsyncSession, data: list[CategorySeed], reset: bool = False
) -> int:
    """Seed heritage categories into the database.

    Args:
        db: Async database session.
        data: List of validated category seed data.
        reset: If True, delete existing categories before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(HeritageCategory))
        print("  Deleted existing categories")

    count = 0
    for item in data:
        # Check if exists
        result = await db.execute(
            select(HeritageCategory).where(HeritageCategory.name == item.name)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Update
            existing.name_zh = item.name_zh
            existing.description = item.description
            print(f"  Updated: {item.name}")
        else:
            # Insert
            category = HeritageCategory(
                name=item.name,
                name_zh=item.name_zh,
                description=item.description,
            )
            db.add(category)
            print(f"  Created: {item.name}")
            count += 1

    return count


async def seed_sites(
    db: AsyncSession, data: list[SiteSeed], reset: bool = False
) -> int:
    """Seed heritage sites into the database.

    Args:
        db: Async database session.
        data: List of validated site seed data.
        reset: If True, delete existing sites before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(HeritageSite))
        print("  Deleted existing sites")

    count = 0
    for item in data:
        # Get category ID
        category_id = None
        if item.category_name:
            result = await db.execute(
                select(HeritageCategory).where(
                    HeritageCategory.name == item.category_name
                )
            )
            category = result.scalar_one_or_none()
            if category:
                category_id = category.id

        # Check if exists
        result = await db.execute(
            select(HeritageSite).where(HeritageSite.slug == item.slug)
        )
        existing = result.scalar_one_or_none()

        site_data: dict[str, Any] = {
            "name": item.name,
            "name_zh": item.name_zh,
            "slug": item.slug,
            "address": item.address,
            "city": item.city,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "description": item.description,
            "description_zh": item.description_zh,
            "history": item.history,
            "history_zh": item.history_zh,
            "featured_image": item.featured_image,
            "images": item.images,
            "designation_level": item.designation_level,
            "is_published": item.is_published,
            "category_id": category_id,
        }

        # Parse designation_date if present
        if item.designation_date:
            site_data["designation_date"] = datetime.fromisoformat(
                item.designation_date
            )

        if existing:
            # Update
            for key, value in site_data.items():
                setattr(existing, key, value)
            print(f"  Updated: {item.name_zh}")
        else:
            # Insert
            site = HeritageSite(**site_data)
            db.add(site)
            print(f"  Created: {item.name_zh}")
            count += 1

    return count


async def seed_visit_info(
    db: AsyncSession, data: list[VisitInfoSeed], reset: bool = False
) -> int:
    """Seed visit information into the database.

    Args:
        db: Async database session.
        data: List of validated visit info seed data.
        reset: If True, delete existing visit info before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(VisitInfo))
        print("  Deleted existing visit info")

    count = 0
    for item in data:
        # Check if exists
        result = await db.execute(
            select(VisitInfo).where(VisitInfo.section == item.section)
        )
        existing = result.scalar_one_or_none()

        info_data: dict[str, Any] = {
            "section": item.section,
            "title": item.title,
            "title_zh": item.title_zh,
            "content": item.content,
            "content_zh": item.content_zh,
            "extra_data": item.extra_data,  # Already validated as JSON by Pydantic
            "display_order": item.display_order,
            "is_active": item.is_active,
        }

        if existing:
            # Update
            for key, value in info_data.items():
                setattr(existing, key, value)
            print(f"  Updated: {item.section}")
        else:
            # Insert
            info = VisitInfo(**info_data)
            db.add(info)
            print(f"  Created: {item.section}")
            count += 1

    return count


async def seed_timeline(
    db: AsyncSession, data: list[TimelineEventSeed], reset: bool = False
) -> int:
    """Seed timeline events into the database.

    Args:
        db: Async database session.
        data: List of validated timeline event seed data.
        reset: If True, delete existing timeline events before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(TimelineEvent))
        print("  Deleted existing timeline events")

    count = 0
    for item in data:
        # Check if exists (by year and title)
        result = await db.execute(
            select(TimelineEvent).where(
                TimelineEvent.year == item.year,
                TimelineEvent.title == item.title,
            )
        )
        existing = result.scalar_one_or_none()

        event_data: dict[str, Any] = {
            "year": item.year,
            "month": item.month,
            "day": item.day,
            "era": item.era,
            "era_year": item.era_year,
            "title": item.title,
            "title_zh": item.title_zh,
            "description": item.description,
            "description_zh": item.description_zh,
            "image": item.image,
            "category": item.category,
            "importance": item.importance,
            "is_published": item.is_published,
        }

        if existing:
            # Update
            for key, value in event_data.items():
                setattr(existing, key, value)
            print(f"  Updated: {item.year} - {item.title_zh}")
        else:
            # Insert
            event = TimelineEvent(**event_data)
            db.add(event)
            print(f"  Created: {item.year} - {item.title_zh}")
            count += 1

    return count


async def seed_news(db: AsyncSession, data: list[NewsSeed], reset: bool = False) -> int:
    """Seed news articles into the database.

    Args:
        db: Async database session.
        data: List of validated news seed data.
        reset: If True, delete existing news before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(News))
        print("  Deleted existing news")

    count = 0
    for item in data:
        # Check if exists
        result = await db.execute(select(News).where(News.slug == item.slug))
        existing = result.scalar_one_or_none()

        news_data: dict[str, Any] = {
            "title": item.title,
            "title_zh": item.title_zh,
            "slug": item.slug,
            "summary": item.summary,
            "summary_zh": item.summary_zh,
            "content": item.content,
            "content_zh": item.content_zh,
            "featured_image": item.featured_image,
            "images": item.images,
            "category": item.category,
            "is_published": item.is_published,
        }

        # Parse published_at if present
        if item.published_at:
            news_data["published_at"] = datetime.fromisoformat(
                item.published_at.replace("Z", "+00:00")
            )

        if existing:
            # Update
            for key, value in news_data.items():
                setattr(existing, key, value)
            print(f"  Updated: {item.slug}")
        else:
            # Insert
            news = News(**news_data)
            db.add(news)
            print(f"  Created: {item.slug}")
            count += 1

    return count


async def seed_media(
    db: AsyncSession, data: list[MediaFileSeed], reset: bool = False
) -> int:
    """Seed media files metadata into the database.

    Args:
        db: Async database session.
        data: List of validated media file seed data.
        reset: If True, delete existing media files before seeding.

    Returns:
        Number of new records created.
    """
    if reset:
        await db.execute(delete(MediaFile))
        print("  Deleted existing media files")

    count = 0
    for item in data:
        # Check if exists
        result = await db.execute(
            select(MediaFile).where(MediaFile.s3_key == item.s3_key)
        )
        existing = result.scalar_one_or_none()

        media_data: dict[str, Any] = {
            "filename": item.filename,
            "original_filename": item.original_filename,
            "s3_key": item.s3_key,
            "public_url": item.public_url,
            "content_type": item.content_type,
            "file_size": item.file_size,
            "category": item.category,
            "folder": item.folder,
            "alt_text": item.alt_text,
            "alt_text_zh": item.alt_text_zh,
            "caption": item.caption,
            "caption_zh": item.caption_zh,
            "width": item.width,
            "height": item.height,
        }

        if existing:
            # Update
            for key, value in media_data.items():
                setattr(existing, key, value)
            print(f"  Updated: {item.filename}")
        else:
            # Insert
            media = MediaFile(**media_data)
            db.add(media)
            print(f"  Created: {item.filename}")
            count += 1

    return count


# =============================================================================
# Main Function
# =============================================================================


async def main(
    tables: list[str] | None = None,
    reset: bool = False,
    dry_run: bool = False,
) -> None:
    """Main seeding function.

    Args:
        tables: Optional list of table names to seed. If None, seeds all tables.
        reset: If True, delete existing data before seeding (destructive).
        dry_run: If True, show what would be done without making changes.

    Raises:
        ValidationError: If seed data doesn't match expected schema.
        IntegrityError: If database constraints are violated.
        OperationalError: If database connection fails.
    """
    # Load and validate seed data
    try:
        seed_data = load_seed_data()
    except ValidationError as e:
        print("\nSeed data validation failed:")
        for error in e.errors():
            location = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  {location}: {error['msg']}")
        raise
    except json.JSONDecodeError as e:
        print(f"\nInvalid JSON in seed data file: {e}")
        raise
    except FileNotFoundError:
        print(f"\nSeed data file not found: {SEED_DATA_PATH}")
        raise

    # Define available seeders with their corresponding data attributes
    seeders: dict[str, tuple[str, Any]] = {
        "categories": ("heritage_categories", seed_categories),
        "sites": ("heritage_sites", seed_sites),
        "visit_info": ("visit_info", seed_visit_info),
        "timeline": ("timeline_events", seed_timeline),
        "news": ("news", seed_news),
        "media": ("media_files", seed_media),
    }

    # Filter tables if specified
    if tables:
        seeders = {k: v for k, v in seeders.items() if k in tables}

    if not seeders:
        print("No valid tables specified")
        return

    print(f"\n{'=' * 50}")
    print(f"Seeding database {'(DRY RUN)' if dry_run else ''}")
    print(f"Tables: {', '.join(seeders.keys())}")
    print(f"Mode: {'RESET' if reset else 'UPSERT'}")
    print(f"{'=' * 50}\n")

    if dry_run:
        print("Dry run mode - no changes will be made\n")
        for name, (data_key, _) in seeders.items():
            data = getattr(seed_data, data_key, [])
            print(f"{name}: {len(data)} records would be processed")
        return

    async with AsyncSessionLocal() as db:
        try:
            total_created = 0

            for name, (data_key, seeder_func) in seeders.items():
                print(f"\n[{name.upper()}]")
                data = getattr(seed_data, data_key, [])
                if not data:
                    print("  No data to seed")
                    continue

                created = await seeder_func(db, data, reset=reset)
                total_created += created

            await db.commit()

            print(f"\n{'=' * 50}")
            print(f"Seeding completed! {total_created} new records created.")
            print(f"{'=' * 50}\n")

        except IntegrityError as e:
            await db.rollback()
            print(f"\nDatabase integrity error: {e.orig}")
            print("This may indicate duplicate data or foreign key violations.")
            raise
        except OperationalError as e:
            await db.rollback()
            print(f"\nDatabase connection error: {e.orig}")
            print("Check that the database is running and accessible.")
            raise
        except SQLAlchemyError as e:
            await db.rollback()
            print(f"\nDatabase error during seeding: {e}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed database with initial data")
    parser.add_argument(
        "--tables",
        type=str,
        help=(
            "Comma-separated list of tables to seed "
            "(categories,sites,visit_info,timeline,news,media)"
        ),
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing data before seeding (WARNING: destructive)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    tables = args.tables.split(",") if args.tables else None

    asyncio.run(main(tables=tables, reset=args.reset, dry_run=args.dry_run))
