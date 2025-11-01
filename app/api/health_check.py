from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy import text
from app.core.database import get_uow

router = APIRouter()

@router.get("/ping",summary="Check Network Connection")
async def ping():
    """
    CHeck Network connection
    """
    return {"status":"ok"}

@router.get("/db",summary="Check the database connection")
async def check_db_connection(
    session:AsyncSession=Depends(get_uow)
):
    """
    Check db connection
    """
    try:
        await session.execute(text("SELECT 1"))
        return {"db_status":"ok"}
    except OperationalError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Could not connect to the database: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred during DB check: {e}"
        ) from e
    

