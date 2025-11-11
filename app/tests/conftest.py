import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, Client
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
    engine = create_async_engine(settings.DATABASE_URL, echo=False)

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

@pytest.fixture(scope="function")
def test_client_sync(test_engine) -> Generator[Client, None, None]:
    """
    A fixture that provides a SYNCHRONOUS test client for testing 'def' endpoints.
    """

    from sqlalchemy.orm import sessionmaker
    TestingSessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    def override_get_sync_db():
        db = TestingSessionLocalSync()
        try:
            yield db
        finally:
            db.close()

    from app.core.db_sync import get_sync_db
    app.dependency_overrides[get_sync_db] = override_get_sync_db

    from fastapi.testclient import TestClient
    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()