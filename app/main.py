"""
Creation Factory file
"""

from fastapi import FastAPI


def create_app()->FastAPI:
    """
    Create app flow
    """

    app = FastAPI(
        title="DocuQuery",
        description="RAG",
        version="1.0.0"
    )

    @app.get("/health")
    def health_check():
        return {'message':'i am alive'}
    
    return app

app = create_app()
