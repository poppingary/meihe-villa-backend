"""
Database Seeder Script for Meihe Villa Backend

This script loads seed data from seed_data.json and populates the database.
Run with: uv run python data/seeds/seed_database.py
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database import AsyncSessionLocal, engine
from app.models.heritage import HeritageCategory, HeritageSite
from app.models.news import News
from app.models.visit_info import VisitInfo
from app.models.timeline import TimelineEvent


async def load_seed_data() -> dict:
    """Load seed data from JSON file."""
    seed_file = Path(__file__).parent / "seed_data.json"
    with open(seed_file, "r", encoding="utf-8") as f:
        return json.load(f)


async def seed_categories(session: AsyncSession, categories: list[dict]) -> dict[str, int]:
    """Seed heritage categories and return mapping of name to id."""
    category_map = {}

    for cat_data in categories:
        # Check if category already exists
        result = await session.execute(
            select(HeritageCategory).where(HeritageCategory.name == cat_data["name"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Category '{cat_data['name']}' already exists (id={existing.id})")
            category_map[cat_data["name"]] = existing.id
        else:
            category = HeritageCategory(
                name=cat_data["name"],
                name_zh=cat_data["name_zh"],
                description=cat_data.get("description")
            )
            session.add(category)
            await session.flush()
            print(f"  Created category '{cat_data['name']}' (id={category.id})")
            category_map[cat_data["name"]] = category.id

    return category_map


async def seed_sites(session: AsyncSession, sites: list[dict], category_map: dict[str, int]) -> None:
    """Seed heritage sites."""
    for site_data in sites:
        # Check if site already exists
        result = await session.execute(
            select(HeritageSite).where(HeritageSite.slug == site_data["slug"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Site '{site_data['name']}' already exists (id={existing.id})")
            continue

        # Parse designation_date if provided
        designation_date = None
        if site_data.get("designation_date"):
            # Handle both date-only and full datetime strings
            date_str = site_data["designation_date"]
            if "T" in date_str:
                designation_date = datetime.fromisoformat(date_str)
            else:
                designation_date = datetime.fromisoformat(f"{date_str}T00:00:00")

        site = HeritageSite(
            name=site_data["name"],
            name_zh=site_data["name_zh"],
            slug=site_data["slug"],
            address=site_data.get("address"),
            city=site_data.get("city"),
            latitude=site_data.get("latitude"),
            longitude=site_data.get("longitude"),
            description=site_data.get("description"),
            description_zh=site_data.get("description_zh"),
            history=site_data.get("history"),
            history_zh=site_data.get("history_zh"),
            featured_image=site_data.get("featured_image"),
            images=site_data.get("images"),
            designation_level=site_data.get("designation_level"),
            designation_date=designation_date,
            is_published=site_data.get("is_published", True),
            category_id=site_data.get("category_id")
        )
        session.add(site)
        await session.flush()
        print(f"  Created site '{site_data['name']}' (id={site.id})")


async def seed_news(session: AsyncSession, news_list: list[dict]) -> None:
    """Seed news articles."""
    for news_data in news_list:
        # Check if news already exists
        result = await session.execute(
            select(News).where(News.slug == news_data["slug"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  News '{news_data['title']}' already exists (id={existing.id})")
            continue

        # Parse published_at if provided
        published_at = None
        if news_data.get("published_at"):
            published_at = datetime.fromisoformat(news_data["published_at"])

        news = News(
            title=news_data["title"],
            title_zh=news_data["title_zh"],
            slug=news_data["slug"],
            summary=news_data.get("summary"),
            summary_zh=news_data.get("summary_zh"),
            content=news_data.get("content"),
            content_zh=news_data.get("content_zh"),
            featured_image=news_data.get("featured_image"),
            category=news_data.get("category"),
            is_published=news_data.get("is_published", True),
            published_at=published_at,
        )
        session.add(news)
        await session.flush()
        print(f"  Created news '{news_data['title']}' (id={news.id})")


async def seed_visit_info(session: AsyncSession, visit_info_list: list[dict]) -> None:
    """Seed visit information."""
    for info_data in visit_info_list:
        # Check if visit info already exists
        result = await session.execute(
            select(VisitInfo).where(VisitInfo.section == info_data["section"])
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Visit info '{info_data['section']}' already exists (id={existing.id})")
            continue

        info = VisitInfo(
            section=info_data["section"],
            title=info_data["title"],
            title_zh=info_data["title_zh"],
            content=info_data.get("content"),
            content_zh=info_data.get("content_zh"),
            extra_data=info_data.get("extra_data"),
            display_order=info_data.get("display_order", 0),
            is_active=info_data.get("is_active", True),
        )
        session.add(info)
        await session.flush()
        print(f"  Created visit info '{info_data['section']}' (id={info.id})")


async def seed_timeline(session: AsyncSession, events_list: list[dict]) -> None:
    """Seed timeline events."""
    for event_data in events_list:
        # Check if event already exists by year and title
        result = await session.execute(
            select(TimelineEvent).where(
                TimelineEvent.year == event_data["year"],
                TimelineEvent.title == event_data["title"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  Timeline event '{event_data['year']} - {event_data['title']}' already exists (id={existing.id})")
            continue

        event = TimelineEvent(
            year=event_data["year"],
            month=event_data.get("month"),
            day=event_data.get("day"),
            era=event_data.get("era"),
            era_year=event_data.get("era_year"),
            title=event_data["title"],
            title_zh=event_data["title_zh"],
            description=event_data.get("description"),
            description_zh=event_data.get("description_zh"),
            image=event_data.get("image"),
            category=event_data.get("category"),
            importance=event_data.get("importance", "normal"),
            is_published=event_data.get("is_published", True),
        )
        session.add(event)
        await session.flush()
        print(f"  Created timeline event '{event_data['year']} - {event_data['title']}' (id={event.id})")


async def main():
    """Main seeding function."""
    print("=" * 50)
    print("Meihe Villa Database Seeder")
    print("=" * 50)

    # Load seed data
    print("\nLoading seed data...")
    seed_data = await load_seed_data()
    print(f"  Found {len(seed_data.get('categories', []))} categories")
    print(f"  Found {len(seed_data.get('sites', []))} sites")
    print(f"  Found {len(seed_data.get('news', []))} news articles")
    print(f"  Found {len(seed_data.get('visit_info', []))} visit info sections")
    print(f"  Found {len(seed_data.get('timeline_events', []))} timeline events")

    # Create database session
    async with AsyncSessionLocal() as session:
        try:
            # Seed categories
            print("\nSeeding categories...")
            category_map = await seed_categories(session, seed_data.get("categories", []))

            # Seed sites
            print("\nSeeding sites...")
            await seed_sites(session, seed_data.get("sites", []), category_map)

            # Seed news
            print("\nSeeding news...")
            await seed_news(session, seed_data.get("news", []))

            # Seed visit info
            print("\nSeeding visit info...")
            await seed_visit_info(session, seed_data.get("visit_info", []))

            # Seed timeline
            print("\nSeeding timeline events...")
            await seed_timeline(session, seed_data.get("timeline_events", []))

            # Commit all changes
            await session.commit()
            print("\n" + "=" * 50)
            print("Database seeding completed successfully!")
            print("=" * 50)

        except Exception as e:
            await session.rollback()
            print(f"\nError during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
