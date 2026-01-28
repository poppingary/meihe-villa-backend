"""Pytest fixtures for testing."""

import uuid as uuid_module

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, String, TypeDecorator
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.deps import get_db
from app.database import Base
from app.main import app

# Use SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses String(36) for SQLite storage, handles uuid.UUID objects properly.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid_module.UUID):
                return str(value)
            return str(uuid_module.UUID(value))
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, uuid_module.UUID):
                return value
            return uuid_module.UUID(value)
        return value


# Monkey-patch the PostgreSQL UUID to use our GUID for SQLite
# This must happen before models are imported/used
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

# Store original for restoration if needed
_original_uuid_init = PG_UUID.__init__


def _patched_uuid_init(self, as_uuid=False, *args, **kwargs):
    # For SQLite testing, use String implementation
    self.impl = String(36)
    self.as_uuid = as_uuid
    self.cache_ok = True


# Apply the patch
PG_UUID.__init__ = _patched_uuid_init


def _patched_result_processor(self, dialect, coltype):
    if self.as_uuid:

        def process(value):
            if value is not None:
                if isinstance(value, uuid_module.UUID):
                    return value
                return uuid_module.UUID(value)
            return value

        return process
    return None


def _patched_bind_processor(self, dialect):
    if self.as_uuid:

        def process(value):
            if value is not None:
                if isinstance(value, uuid_module.UUID):
                    return str(value)
                return str(value)
            return value

        return process
    return None


PG_UUID.result_processor = _patched_result_processor
PG_UUID.bind_processor = _patched_bind_processor


# Register UUID adapter for SQLite (synchronous connection for listeners)
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key support for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
async def async_engine():
    """Create an async engine for testing."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(async_engine):
    """Create a database session for testing."""
    async_session = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with async_session() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Create a test client with database session override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
