from app.models.chunk import Chunk
from app.repositories.cached_query_repository import CachedQueryRepository
from app.schemas.query import QueryRequest, QueryResponse, Source
from app.repositories.chunk_repository import ChunkRepository
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.core.config import get_embedding_model, get_generative_model, LLM_QUERY_DURATION

logger = logging.getLogger(__name__)


class QueryService:
    """
    Contains the business logic for the RAG (Retrieval-Augmented Generation) process.
    """
    def __init__(self, chunk_repo: ChunkRepository, cached_query_repo: CachedQueryRepository):
        self.chunk_repo = chunk_repo
        self.cached_query_repo = cached_query_repo

    def answer_question(self, query: QueryRequest) -> QueryResponse:
        """
        Orchestrates the RAG pipeline to answer a user's question.
        """
        try:

            logger.info(f"Embedding question for cache lookup: '{query.question}'")

            embedding_model = get_embedding_model()

            question_embedding = next(embedding_model.embed(query.question))
            logger.debug(f"Generated embedding type: {type(question_embedding)}, shape: {getattr(question_embedding, 'shape', 'N/A')}")

            cached_result = self.cached_query_repo.find_similar_query(question_embedding.tolist())

            if cached_result:
                logger.info(f"Semantic cache HIT. Found similar question: '{cached_result.question_text}'")
                return QueryResponse(
                    answer=cached_result.response_answer,
                    sources=[Source(
                        filename=chunk.chunk_metadata.get("source_filename", "Unknown"),
                        snippet=chunk.chunk_text
                    ) for chunk in cached_result.source_chunks]
                )

            logger.info("Semantic cache MISS. Proceeding with full RAG pipeline.")

            answer, source_chunks = self._perform_rag(query, question_embedding)

            logger.info("Populating semantic cache with new response.")

            self.cached_query_repo.save_query(
                question_text=query.question,
                query_embedding=question_embedding.tolist() if hasattr(question_embedding, 'tolist') else question_embedding,
                answer=answer,
                source_chunks=source_chunks
            )

            return QueryResponse(
                answer=answer,
                sources=[Source(
                    filename=chunk.chunk_metadata.get("source_filename", "Unknown"),
                    snippet=chunk.chunk_text
                ) for chunk in source_chunks]
            )
        
        except SQLAlchemyError as e:
            logger.exception(f"A database error occurred during the query process => {e}.")
            return QueryResponse(
                answer="I'm sorry, but I encountered a database error while trying to answer your question. Please try again later.",
                sources=[]
            )
        except Exception as e:
            logger.exception("An unexpected error occurred in the query service.")
            return QueryResponse(
                answer=f"An unexpected error occurred: {e}",
                sources=[]
            )
    
    def _perform_rag(self, query: QueryRequest, question_embedding: list[float]) -> tuple[str, list[Chunk]]:
        """
        Performs the core RAG logic and returns the answer string AND the source chunk objects.
        """
        logger.info("Finding relevant chunks in the database...")
        relevant_chunks = self.chunk_repo.find_relevant_chunks_sync(question_embedding)

        if not relevant_chunks:
            return "I could not find any relevant information in the knowledge base to answer your question.", []

        logger.info(f"Found {len(relevant_chunks)} relevant chunks.")
        context = "\n---\n".join([chunk.chunk_text for chunk in relevant_chunks])
        
        prompt = f"""
        You are a helpful AI assistant for developers. Your name is DocuQuery.
        Answer the user's question based ONLY on the following context.
        If the context does not contain the answer, say "I'm sorry, I cannot answer this question based on the provided documents."

        CONTEXT:
        {context}

        QUESTION:
        {query.question}

        ANSWER:
        """
                
        logger.info("Sending prompt to Gemini for generation...")

        try:
            generative_model = get_generative_model()
            with LLM_QUERY_DURATION.time():
                response = generative_model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            logger.exception("Error calling Gemini API.")
            answer = f"An error occurred while generating the answer with the Gemini API: {e}"

        return answer, relevant_chunks
    