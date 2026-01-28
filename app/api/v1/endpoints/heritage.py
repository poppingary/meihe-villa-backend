"""Heritage sites API endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession
from app.models.heritage import HeritageCategory, HeritageSite
from app.schemas.heritage import (
    HeritageCategoryCreate,
    HeritageCategoryResponse,
    HeritageSiteCreate,
    HeritageSiteResponse,
    HeritageSiteUpdate,
)

router = APIRouter()


# Heritage Sites endpoints
@router.get("/sites", response_model=list[HeritageSiteResponse])
async def list_heritage_sites(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    city: str | None = None,
    category_id: int | None = None,
    published_only: bool = True,
):
    """List heritage sites with optional filtering."""
    query = select(HeritageSite).options(selectinload(HeritageSite.category))

    if published_only:
        query = query.where(HeritageSite.is_published == True)  # noqa: E712
    if city:
        query = query.where(HeritageSite.city == city)
    if category_id:
        query = query.where(HeritageSite.category_id == category_id)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/sites/{site_id}", response_model=HeritageSiteResponse)
async def get_heritage_site(db: DbSession, site_id: int):
    """Get a heritage site by ID."""
    query = (
        select(HeritageSite)
        .options(selectinload(HeritageSite.category))
        .where(HeritageSite.id == site_id)
    )
    result = await db.execute(query)
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage site not found",
        )
    return site


@router.get("/sites/slug/{slug}", response_model=HeritageSiteResponse)
async def get_heritage_site_by_slug(db: DbSession, slug: str):
    """Get a heritage site by slug."""
    query = (
        select(HeritageSite)
        .options(selectinload(HeritageSite.category))
        .where(HeritageSite.slug == slug)
    )
    result = await db.execute(query)
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage site not found",
        )
    return site


@router.post("/sites", response_model=HeritageSiteResponse, status_code=status.HTTP_201_CREATED)
async def create_heritage_site(db: DbSession, site_in: HeritageSiteCreate):
    """Create a new heritage site."""
    site = HeritageSite(**site_in.model_dump())
    db.add(site)
    await db.flush()
    await db.refresh(site, attribute_names=["category"])
    return site


@router.patch("/sites/{site_id}", response_model=HeritageSiteResponse)
async def update_heritage_site(
    db: DbSession,
    site_id: int,
    site_in: HeritageSiteUpdate,
):
    """Update a heritage site."""
    query = select(HeritageSite).where(HeritageSite.id == site_id)
    result = await db.execute(query)
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage site not found",
        )

    update_data = site_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(site, field, value)

    await db.flush()
    # Refresh all attributes including updated_at and category
    await db.refresh(site)
    return site


@router.delete("/sites/{site_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_heritage_site(db: DbSession, site_id: int):
    """Delete a heritage site."""
    query = select(HeritageSite).where(HeritageSite.id == site_id)
    result = await db.execute(query)
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Heritage site not found",
        )
    await db.delete(site)


# Heritage Categories endpoints
@router.get("/categories", response_model=list[HeritageCategoryResponse])
async def list_heritage_categories(db: DbSession):
    """List all heritage categories."""
    query = select(HeritageCategory)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/categories", response_model=HeritageCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_heritage_category(db: DbSession, category_in: HeritageCategoryCreate):
    """Create a new heritage category."""
    category = HeritageCategory(**category_in.model_dump())
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category
