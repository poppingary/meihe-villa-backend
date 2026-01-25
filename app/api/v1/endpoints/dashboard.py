"""Dashboard statistics API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import DbSession
from app.models.heritage import HeritageCategory, HeritageSite
from app.models.news import News
from app.models.timeline import TimelineEvent
from app.models.visit_info import VisitInfo


class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    total_sites: int
    published_sites: int
    draft_sites: int
    total_categories: int
    total_news: int
    published_news: int
    total_timeline_events: int
    published_timeline_events: int
    total_visit_info: int
    active_visit_info: int


class RecentActivity(BaseModel):
    """Recent activity item."""

    type: str
    title: str
    action: str
    timestamp: str


router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: DbSession):
    """Get dashboard statistics."""
    # Heritage sites stats
    total_sites_query = select(func.count(HeritageSite.id))
    total_sites_result = await db.execute(total_sites_query)
    total_sites = total_sites_result.scalar() or 0

    published_sites_query = select(func.count(HeritageSite.id)).where(
        HeritageSite.is_published == True  # noqa: E712
    )
    published_sites_result = await db.execute(published_sites_query)
    published_sites = published_sites_result.scalar() or 0

    # Categories stats
    categories_query = select(func.count(HeritageCategory.id))
    categories_result = await db.execute(categories_query)
    total_categories = categories_result.scalar() or 0

    # News stats
    total_news_query = select(func.count(News.id))
    total_news_result = await db.execute(total_news_query)
    total_news = total_news_result.scalar() or 0

    published_news_query = select(func.count(News.id)).where(
        News.is_published == True  # noqa: E712
    )
    published_news_result = await db.execute(published_news_query)
    published_news = published_news_result.scalar() or 0

    # Timeline stats
    total_timeline_query = select(func.count(TimelineEvent.id))
    total_timeline_result = await db.execute(total_timeline_query)
    total_timeline = total_timeline_result.scalar() or 0

    published_timeline_query = select(func.count(TimelineEvent.id)).where(
        TimelineEvent.is_published == True  # noqa: E712
    )
    published_timeline_result = await db.execute(published_timeline_query)
    published_timeline = published_timeline_result.scalar() or 0

    # Visit info stats
    total_visit_query = select(func.count(VisitInfo.id))
    total_visit_result = await db.execute(total_visit_query)
    total_visit = total_visit_result.scalar() or 0

    active_visit_query = select(func.count(VisitInfo.id)).where(
        VisitInfo.is_active == True  # noqa: E712
    )
    active_visit_result = await db.execute(active_visit_query)
    active_visit = active_visit_result.scalar() or 0

    return DashboardStats(
        total_sites=total_sites,
        published_sites=published_sites,
        draft_sites=total_sites - published_sites,
        total_categories=total_categories,
        total_news=total_news,
        published_news=published_news,
        total_timeline_events=total_timeline,
        published_timeline_events=published_timeline,
        total_visit_info=total_visit,
        active_visit_info=active_visit,
    )
