"""Pydantic schemas for heritage sites."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


# Heritage Category schemas
class HeritageCategoryBase(BaseModel):
    """Base schema for heritage category."""

    name: str
    name_zh: str
    description: str | None = None


class HeritageCategoryCreate(HeritageCategoryBase):
    """Schema for creating a heritage category."""

    pass


class HeritageCategoryResponse(HeritageCategoryBase):
    """Schema for heritage category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# Heritage Site schemas
class HeritageSiteBase(BaseModel):
    """Base schema for heritage site."""

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
    designation_date: datetime | None = None
    is_published: bool = False
    category_id: int | None = None


class HeritageSiteCreate(HeritageSiteBase):
    """Schema for creating a heritage site."""

    pass


class HeritageSiteUpdate(BaseModel):
    """Schema for updating a heritage site (all fields optional)."""

    name: str | None = None
    name_zh: str | None = None
    slug: str | None = None
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
    designation_date: datetime | None = None
    is_published: bool | None = None
    category_id: int | None = None


class HeritageSiteResponse(HeritageSiteBase):
    """Schema for heritage site response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    category: HeritageCategoryResponse | None = None
    created_at: datetime
    updated_at: datetime
