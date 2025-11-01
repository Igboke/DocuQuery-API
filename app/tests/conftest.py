import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from httpx._transports.asgi import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.database import get_uow
from app.models.base import Base
from app.core.config import settings


@pytest.fixture(scope="function")
async def test_engine():
    """
    Creates a test database engine for each test.
    """
    engine = create_async_engine(settings.TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_client(test_engine) -> AsyncGenerator[AsyncClient, None]:
    """
    A fixture that sets up the test database and provides an HTTP client.
    Each test gets its own client and database session.
    """
    TestingSessionLocal = async_sessionmaker(
        autoflush=False,
        autocommit=False,
        bind=test_engine,
        expire_on_commit=False
    )

    async def override_get_uow() -> AsyncGenerator[AsyncSession, None]:
        """
        A dependency override that provides a session to the test database.
        Each request gets a fresh session that will be rolled back after the test.
        """
        async with TestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_uow] = override_get_uow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()