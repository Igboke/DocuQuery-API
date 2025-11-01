import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker,AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from .config import settings

engine = create_async_engine(settings.DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=True,
    expire_on_commit=False
)

class UnitOfWork:
    """
    Single Unit of Work
    """
    def __init__(self):
        self.session_maker = AsyncSessionLocal
    
    async def __aenter__(self)->AsyncSession:
        self.session = self.session_maker()

        return self.session
    
    async def __aexit__(self,exc_type,exc_val,exc_tb):
        if exc_type:
            await self.session.rollback()

        else:
            try:
                await self.session.commit()

            except SQLAlchemyError:
                await self.session.rollback()
            
                raise
            except exc_type:
                await self.session.rollback()

                raise
            finally:
                await self.session.close()

async def get_uow()->AsyncGenerator[AsyncSession,None]:
    """
    Unit of work
    """

    uow = UnitOfWork()

    async with uow as session:
        yield session
        

    
