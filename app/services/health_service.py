from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
import logging

logger = logging.getLogger(__name__)

class HealthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def check_db_connection(self) -> dict:
        """
        Checks the database connection by executing a simple query.
        """
        try:
            await self.session.execute(text("SELECT 1"))
            return {"db_status": "ok"}
        except OperationalError as e:
            logger.error(f"Health check failed: Database operational error: {e}")
            raise
        except Exception as e:
            logger.error(f"Health check failed: Unexpected error: {e}")
            raise
