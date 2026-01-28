"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.config import get_settings
from app.database import AsyncSessionLocal

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title=settings.app_name,
    description="API for Meihe Villa - Taiwan Heritage Sites (台灣古蹟網站)",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity verification."""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "checks": {
            "database": "unknown",
        },
    }

    # Check database connectivity
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"error: {type(e).__name__}"
        return JSONResponse(status_code=503, content=health_status)

    return health_status


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Meihe Villa API",
        "docs": "/docs",
        "health": "/health",
    }
