"""
Creation Factory file
"""

from fastapi import FastAPI
from app.api import health_check

def create_app()->FastAPI:
    """
    Create app flow
    """

    app = FastAPI(
        title="DocuQuery",
        description="RAG",
        version="1.0.0"
    )

    app.include_router(health_check.router,prefix="/health",tags=["Health"])


    @app.get("/health")
    def health_check_():
        return {'message':'i am alive'}
    
    return app

app = create_app()
