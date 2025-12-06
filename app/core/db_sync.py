from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from app.core.config import settings

SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "").replace("+aiosqlite", "")

engine = create_engine(SYNC_DATABASE_URL)

SessionLocalSync = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_sync_db():
    """
    Provides a synchronous database session for use in Celery tasks.
    """
    db = SessionLocalSync()
    try:
        yield db
    finally:
        db.close()


def get_sync_db_session():
    """
    A FastAPI dependency that provides a synchronous database session.
    It yields the session and ensures it's closed after the request.
    Automatically commits on success and rolls back on exceptions.
    """
    db = SessionLocalSync()
    try:
        yield db
        db.commit() 
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
