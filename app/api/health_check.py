from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError
from app.services.health_service import HealthService
from app.dependencies import get_health_service

router = APIRouter()

@router.get("/ping",summary="Check Network Connection")
async def ping():
    return {"status":"ok"}

@router.get("/db",summary="Check the database connection")
async def check_db_connection(
    service: HealthService = Depends(get_health_service)
):
    try:
        return await service.check_db_connection()
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
    

