"""
Creation Factory file
"""

from fastapi import APIRouter, FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.logging_config import setup_logging
from app.api import health_check
from app.api.v1 import documents as documents_v1
from app.api.v1 import query as query_v1
from starlette_prometheus import PrometheusMiddleware, metrics
from app import limiter

def create_app()->FastAPI:
    """
    Create app flow
    """
    setup_logging()
    
    app = FastAPI(
        title="DocuQuery",
        description="RAG",
        version="1.0.0"
    )

    app.state.limiter = limiter

    app.add_middleware(PrometheusMiddleware)

    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    api_router_v1 = APIRouter(prefix="/api/v1")
    api_router_v1.include_router(documents_v1.router, tags=["Documents"])
    api_router_v1.include_router(query_v1.router, tags=["Query"])
    
    app.include_router(api_router_v1)
    app.include_router(health_check.router,prefix="/health",tags=["Health"])
    app.add_route("/metrics", metrics)


    @app.get("/health")
    def health_check_():
        return {'message':'i am alive'}
    
    return app

app = create_app()
