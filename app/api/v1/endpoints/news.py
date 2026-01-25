"""News API endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.news import News
from app.schemas.news import (
    NewsCreate,
    NewsResponse,
    NewsUpdate,
)

router = APIRouter()


@router.get("", response_model=list[NewsResponse])
async def list_news(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    published_only: bool = True,
):
    """List news with optional filtering."""
    query = select(News)

    if published_only:
        query = query.where(News.is_published == True)  # noqa: E712
    if category:
        query = query.where(News.category == category)

    query = query.order_by(News.published_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news(db: DbSession, news_id: int):
    """Get news by ID."""
    query = select(News).where(News.id == news_id)
    result = await db.execute(query)
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found",
        )
    return news


@router.get("/slug/{slug}", response_model=NewsResponse)
async def get_news_by_slug(db: DbSession, slug: str):
    """Get news by slug."""
    query = select(News).where(News.slug == slug)
    result = await db.execute(query)
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found",
        )
    return news


@router.post("", response_model=NewsResponse, status_code=status.HTTP_201_CREATED)
async def create_news(db: DbSession, news_in: NewsCreate):
    """Create a new news article."""
    news = News(**news_in.model_dump())
    db.add(news)
    await db.flush()
    await db.refresh(news)
    return news


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news(
    db: DbSession,
    news_id: int,
    news_in: NewsUpdate,
):
    """Update a news article."""
    query = select(News).where(News.id == news_id)
    result = await db.execute(query)
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found",
        )

    update_data = news_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(news, field, value)

    await db.flush()
    await db.refresh(news)
    return news


@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news(db: DbSession, news_id: int):
    """Delete a news article."""
    query = select(News).where(News.id == news_id)
    result = await db.execute(query)
    news = result.scalar_one_or_none()
    if not news:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News not found",
        )
    await db.delete(news)
