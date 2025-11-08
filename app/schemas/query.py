from pydantic import BaseModel, Field
from typing import List


class QueryRequest(BaseModel):
    """
    The request model for a user's query.
    """
    question: str = Field(
        ...,
        min_length=3,
        max_length=300,
        description="The natural language question to ask the knowledge base."
    )


class Source(BaseModel):
    """
    Represents a single source document chunk that contributed to the answer.
    """
    filename: str = Field(..., description="The name of the source file.")
    snippet: str = Field(..., description="The specific text snippet from the source file.")


class QueryResponse(BaseModel):
    """
    The successful response model for a query.
    """
    answer: str = Field(..., description="The synthesized natural language answer.")
    sources: List[Source] = Field(..., description="A list of source snippets used to generate the answer.")
    