"""Tests for main API endpoints."""

import pytest


@pytest.mark.asyncio
async def test_root(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Welcome to Meihe Villa API"


@pytest.mark.asyncio
async def test_health(client):
    """Test health check endpoint with database connectivity."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "checks" in data
    assert data["checks"]["database"] == "connected"


@pytest.mark.asyncio
async def test_docs_available(client):
    """Test that OpenAPI docs are available."""
    response = await client.get("/docs")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_heritage_sites_empty(client):
    """Test listing heritage sites when empty."""
    response = await client.get("/api/v1/heritage/sites")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_heritage_categories_empty(client):
    """Test listing heritage categories when empty."""
    response = await client.get("/api/v1/heritage/categories")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_heritage_site_not_found(client):
    """Test getting non-existent heritage site."""
    response = await client.get("/api/v1/heritage/sites/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_heritage_category(client):
    """Test creating a heritage category."""
    category_data = {
        "name": "Temples",
        "name_zh": "寺廟",
        "description": "Buddhist and Taoist temples",
    }
    response = await client.post("/api/v1/heritage/categories", json=category_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Temples"
    assert data["name_zh"] == "寺廟"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_heritage_site(client):
    """Test creating a heritage site."""
    site_data = {
        "name": "Meihe Villa",
        "name_zh": "梅鶴山莊",
        "slug": "meihe-villa",
        "city": "Taipei",
        "description": "A historic villa in Taiwan",
        "is_published": True,
    }
    response = await client.post("/api/v1/heritage/sites", json=site_data)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Meihe Villa"
    assert data["slug"] == "meihe-villa"
    assert "id" in data
