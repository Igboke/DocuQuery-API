from app.schemas.query import QueryRequest, QueryResponse, Source
from app.repositories.chunk_repository import ChunkRepository
import logging
from app.core.config import get_embedding_model, get_generative_model, LLM_QUERY_DURATION

logger = logging.getLogger(__name__)


class QueryService:
    """
    Contains the business logic for the RAG (Retrieval-Augmented Generation) process.
    """
    def __init__(self, chunk_repo: ChunkRepository):
        self.chunk_repo = chunk_repo

    def answer_question(self, query: QueryRequest) -> QueryResponse:
        """
        Orchestrates the RAG pipeline to answer a user's question.
        
        For now, this is a placeholder that returns a fake response.
        """

        logger.info(f"Embedding question: '{query.question}'")
        embedding_model = get_embedding_model()
        question_embedding = next(embedding_model.embed(query.question))

        logger.info("Finding relevant chunks in the database...")
        relevant_chunks = self.chunk_repo.find_relevant_chunks_sync(question_embedding.tolist())

        if not relevant_chunks:
            return QueryResponse(
                answer="I could not find any relevant information in the knowledge base to answer your question.",
                sources=[]
            )

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

        sources = [
            Source(
                filename=chunk.chunk_metadata.get("source_filename", "Unknown"),
                snippet=chunk.chunk_text
            ) for chunk in relevant_chunks
        ]

        return QueryResponse(answer=answer, sources=sources)
    