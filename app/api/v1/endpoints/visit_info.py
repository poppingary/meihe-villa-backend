"""Visit Information API endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.visit_info import VisitInfo
from app.schemas.visit_info import (
    VisitInfoCreate,
    VisitInfoResponse,
    VisitInfoUpdate,
)

router = APIRouter()


@router.get("", response_model=list[VisitInfoResponse])
async def list_visit_info(
    db: DbSession,
    active_only: bool = True,
):
    """List all visit information sections."""
    query = select(VisitInfo)

    if active_only:
        query = query.where(VisitInfo.is_active == True)  # noqa: E712

    query = query.order_by(VisitInfo.display_order)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{info_id}", response_model=VisitInfoResponse)
async def get_visit_info(db: DbSession, info_id: int):
    """Get visit info by ID."""
    query = select(VisitInfo).where(VisitInfo.id == info_id)
    result = await db.execute(query)
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit info not found",
        )
    return info


@router.get("/section/{section}", response_model=VisitInfoResponse)
async def get_visit_info_by_section(db: DbSession, section: str):
    """Get visit info by section name."""
    query = select(VisitInfo).where(VisitInfo.section == section)
    result = await db.execute(query)
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit info not found",
        )
    return info


@router.post("", response_model=VisitInfoResponse, status_code=status.HTTP_201_CREATED)
async def create_visit_info(db: DbSession, info_in: VisitInfoCreate):
    """Create a new visit info section."""
    info = VisitInfo(**info_in.model_dump())
    db.add(info)
    await db.flush()
    await db.refresh(info)
    return info


@router.patch("/{info_id}", response_model=VisitInfoResponse)
async def update_visit_info(
    db: DbSession,
    info_id: int,
    info_in: VisitInfoUpdate,
):
    """Update visit info section."""
    query = select(VisitInfo).where(VisitInfo.id == info_id)
    result = await db.execute(query)
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit info not found",
        )

    update_data = info_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(info, field, value)

    await db.flush()
    await db.refresh(info)
    return info


@router.delete("/{info_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_visit_info(db: DbSession, info_id: int):
    """Delete visit info section."""
    query = select(VisitInfo).where(VisitInfo.id == info_id)
    result = await db.execute(query)
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Visit info not found",
        )
    await db.delete(info)
