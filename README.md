# DocuQuery API

A powerful document intelligence system that enables natural language querying of uploaded documents using advanced vector search and retrieval-augmented generation (RAG) technology.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.120+-green.svg)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-blue.svg)](https://www.postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

DocuQuery API transforms static documents into an intelligent knowledge base, allowing users to ask questions in natural language and receive precise, contextual answers extracted from their document collections.

## Quick Start

Get DocuQuery running in under 5 minutes:

```bash
# Clone the repository
git clone https://github.com/Igboke/DocuQuery-API.git
cd DocuQuery-API

# Copy environment configuration
cp .env.example .env
# Edit .env with your Google API key and other settings

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec api alembic upgrade head

# Verify installation
curl http://localhost:8000/docs
```

Visit http://localhost:8000/docs to explore the interactive API documentation.

## What is DocuQuery API?

### For Beginners
DocuQuery API is like having a smart assistant that reads through all your documents and can instantly answer questions about their content. Upload ZIP files containing documents, ask questions in plain English, and get accurate answers with source citations.

### For Developers
DocuQuery API is a production-ready document intelligence platform built on modern technologies:

- **Vector Database**: Uses PostgreSQL with pgvector extension for semantic search
- **Embedding Models**: Leverages sentence transformers for document vectorization
- **Language Models**: Integrates with Google's Generative AI for answer generation
- **Asynchronous Processing**: Celery-based background task queue for document ingestion
- **Semantic Caching**: Intelligent caching system for improved response times
- **Rate Limiting**: Built-in API protection and usage controls

### Key Features

- **Natural Language Queries**: Ask questions in conversational language
- **Document Upload**: Support for ZIP archives containing multiple document types
- **Semantic Search**: Vector-based similarity search for relevant content retrieval
- **Source Attribution**: Every answer includes references to source documents
- **Background Processing**: Asynchronous document ingestion and indexing
- **Intelligent Caching**: Semantic similarity-based response caching
- **RESTful API**: Clean, well-documented API endpoints
- **Production Ready**: Comprehensive logging, monitoring, and error handling

### Use Cases

- **Knowledge Management**: Create searchable repositories from document collections
- **Research Assistance**: Quickly find relevant information across large document sets
- **Customer Support**: Build intelligent FAQ systems from documentation
- **Legal Document Review**: Efficiently search through contracts and legal documents
- **Academic Research**: Query research papers and academic literature
- **Business Intelligence**: Extract insights from reports and business documents

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │    │   DocuQuery     │    │    External     │
│                 │    │      API        │    │    Services     │
│  Web/Mobile/CLI │◄───┤  (FastAPI)      │◄───┤  Google AI      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
        │     Redis       │    │   PostgreSQL    │    │     Celery      │
        │  (Task Queue)   │◄───┤  (Vector Store) │◄───┤    Workers      │
        └─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Breakdown

- **FastAPI Application**: Handles HTTP requests, authentication, and API routing
- **PostgreSQL + pgvector**: Stores documents, chunks, and vector embeddings
- **Redis**: Message broker for background task queue
- **Celery Workers**: Process document ingestion and embedding generation
- **Google Generative AI**: Provides language model capabilities for answer generation
- **Embedding Models**: Transform text into vector representations for semantic search

### Data Flow

1. **Document Upload**: User uploads ZIP file via API endpoint
2. **Background Processing**: Celery worker extracts and chunks documents
3. **Embedding Generation**: Text chunks are converted to vector embeddings
4. **Storage**: Chunks and embeddings stored in PostgreSQL with vector indexes
5. **Query Processing**: User questions are embedded and matched against document vectors
6. **Answer Generation**: Retrieved contexts are sent to language model for answer synthesis
7. **Response**: User receives answer with source document references

## Installation & Setup

### Prerequisites

- **Docker & Docker Compose**: For the easiest setup experience
- **Python 3.12+**: Required for local development
- **PostgreSQL 16+**: With pgvector extension (handled automatically in Docker)
- **Redis**: For task queue management (included in Docker setup)
- **Google API Key**: Required for generative AI features

### Option A: Docker Compose (Recommended)

The Docker setup provides a complete environment with all dependencies pre-configured:

```bash
# 1. Clone the repository
git clone https://github.com/Igboke/DocuQuery-API.git
cd DocuQuery-API

# 2. Set up environment variables
cp .env.example .env
# Edit .env file with your configuration (see Environment Configuration below)

# 3. Start all services
docker-compose up -d

# 4. Run database migrations
docker-compose exec api alembic upgrade head

# 5. Verify services are running
docker-compose ps
```

### Option B: Local Development Setup

For development or custom deployments:

```bash
# 1. Install Python dependencies
pip install uv
uv pip install ".[test]"

# 2. Set up PostgreSQL with pgvector
# Install PostgreSQL 16+ and the pgvector extension
createdb docuquery_db
psql docuquery_db -c "CREATE EXTENSION vector;"

# 3. Set up Redis
# Install and start Redis server on default port 6379

# 4. Configure environment
cp .env.example .env
# Edit .env with your local database and Redis settings

# 5. Run database migrations
alembic upgrade head

# 6. Start the application
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Start Celery worker (in a separate terminal)
celery -A app.worker.celery worker --loglevel=info
```

### Environment Configuration

Edit your `.env` file with the following required settings:

```bash
# Google API Configuration (Required)
GOOGLE_API_KEY="your-google-api-key-here"

# API Security (Required)
# Generate a secure random string for API authentication
API_KEY="your-secure-api-key-here"

# Database Configuration
DB_USER="marketting"
DB_PASSWORD="password"
DB_HOST="localhost"        # Use "db" for Docker Compose
DB_PORT=5432
DB_NAME="docuquery_db"

# Redis Configuration
REDIS_HOST="localhost"     # Use "redis" for Docker Compose
REDIS_PORT=6379
```

### Database Setup & Migrations

The application uses Alembic for database migrations:

```bash
# Apply all migrations (creates tables and indexes)
alembic upgrade head

# Check migration status
alembic current

# Create new migration (for developers)
alembic revision --autogenerate -m "Description of changes"
```

## API Documentation

### Authentication

All API endpoints require authentication via API key header:

```bash
# Include this header in all requests
X-API-KEY: your-api-key-here
```

### Core Endpoints

#### Document Upload

Upload ZIP files containing documents for processing.

**Endpoint**: `POST /api/v1/documents/upload`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -H "X-API-KEY: your-api-key" \
  -F "file=@documents.zip"
```

**Response**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "documents.zip",
  "status": "PENDING",
}
```

**Supported File Types**: ZIP archives containing text documents (MD), (PDF, DOCX, TXT, etc. to come)

#### Query Documents

Ask natural language questions about uploaded documents.

**Endpoint**: `POST /api/v1/query`

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "X-API-KEY: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic of the uploaded documents?"}'
```

**Response**:
```json
{
  "answer": "The uploaded documents primarily focus on API development best practices, covering topics such as RESTful design patterns, authentication mechanisms, and error handling strategies.",
  "sources": [
    {
      "document_filename": "api-guide.pdf",
      "chunk_text": "API development requires careful consideration of...",
    }
  ]
}
```

#### Health Check

Verify API status and dependencies.

**Endpoint**: `GET /health/ping`

**Endpoint**: `GET /health/db`

### Error Handling

The API uses standard HTTP status codes and provides detailed error messages:

```json
{
  "detail": "Invalid file type. Only ZIP archives are supported.",
  "error_code": "INVALID_FILE_TYPE",
  "timestamp": "2024-11-11T10:30:00Z"
}
```

Common status codes:
- `200`: Success
- `202`: Accepted (background processing started)
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (missing or invalid API key)
- `422`: Validation Error (malformed request data)
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

## Usage Examples

### Basic Document Upload

```python
import requests

with open('documents.zip', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        headers={'X-API-KEY': 'your-api-key'},
        files={'file': f}
    )

job_data = response.json()
print(f"Upload job ID: {job_data['job_id']}")
```

### Querying Documents

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/query',
    headers={
        'X-API-KEY': 'your-api-key',
        'Content-Type': 'application/json'
    },
    json={'question': 'What are the key findings in the research?'}
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents")
```

### JavaScript Integration

```javascript

const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/v1/documents/upload', {
    method: 'POST',
    headers: {
        'X-API-KEY': 'your-api-key'
    },
    body: formData
})
.then(response => response.json())
.then(data => console.log('Upload successful:', data));

fetch('http://localhost:8000/api/v1/query', {
    method: 'POST',
    headers: {
        'X-API-KEY': 'your-api-key',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        question: 'What is the main conclusion?'
    })
})
.then(response => response.json())
.then(data => console.log('Answer:', data.answer));
```

### Rate Limiting

The API includes built-in rate limiting:

- **Query Endpoint**: 5 requests per minute
- **Upload Endpoint**: 3 uploads per minute
- **Rate limit headers** included in responses

```bash

curl -I http://localhost:8000/api/v1/query \
  -H "X-API-KEY: your-api-key"

```

## Development

### Project Structure

```
DocuQuery-API/
├── app/
│   ├── api/                 # API route definitions
│   │   └── v1/             # Version 1 endpoints
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database connections
│   │   └── security.py     # Authentication logic
│   ├── models/             # Database models
│   ├── repositories/       # Data access layer
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   ├── tests/              # Test suite
│   ├── main.py            # Application entry point
│   └── worker.py          # Celery worker tasks
├── alembic/               # Database migrations
├── .github/
│   └── workflows/         # CI/CD pipeline
├── docker-compose.yml     # Service orchestration
├── Dockerfile            # Container definition
└── pyproject.toml        # Python dependencies
```

### Running Tests

```bash
python -m pytest -v

python -m pytest --cov=app --cov-report=html

python -m pytest app/tests/api/v1/test_query.py -v

docker-compose exec api python -m pytest -v
```

### Code Quality Tools

The project uses several tools to maintain code quality:

```bash
mypy app/

black app/
ruff format app/

ruff check app/

bandit -r app/
```

### Contributing Guidelines

1. **Fork the repository** and create a feature branch
2. **Write tests** for new functionality
3. **Ensure all tests pass** and maintain coverage above 80%
4. **Follow code style** guidelines (Black + Ruff)
5. **Update documentation** for user-facing changes
6. **Submit a pull request** with clear description

## Deployment

### Docker Production Setup

For production deployment, use the multi-stage Dockerfile:

```dockerfile
FROM python:3.12-slim as production

RUN adduser --disabled-password --gecos '' appuser

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=appuser:appuser app/ /app/
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables Reference

```bash
GOOGLE_API_KEY=your-google-api-key
API_KEY=your-secure-api-key

DB_HOST=db-server.example.com
DB_PORT=5432
DB_NAME=docuquery_production
DB_USER=docuquery
DB_PASSWORD=secure-password

REDIS_HOST=redis-server.example.com
REDIS_PORT=6379

```

### Scaling Considerations

- **Horizontal Scaling**: Multiple API instances behind a load balancer
- **Worker Scaling**: Scale Celery workers based on queue length
- **Database**: Use read replicas for query-heavy workloads
- **Caching**: Redis cluster for high-availability caching
- **File Storage**: Object storage (S3, GCS) for uploaded documents

### Monitoring & Logging

Built-in monitoring endpoints:

```bash
GET /metrics

GET /health

docker-compose logs api
```

## Advanced Features

### Semantic Caching

DocuQuery includes intelligent caching that recognizes semantically similar questions:

```python
# These questions would share the same cached response
"What is machine learning?"
"Can you explain machine learning?"
"What does ML mean?"
```

Cache configuration:
- **Similarity Threshold**: 0.3 (configurable)

### Vector Search Configuration

Fine-tune search behavior:

```python
VECTOR_SIMILARITY_THRESHOLD = 0.2  # Lower = more permissive
TOP_K_RESULTS = 5                   # Number of chunks to retrieve
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
```

### Background Task Processing

Monitor and manage background tasks:

```bash
# View active workers
celery -A app.worker.celery inspect active

# Monitor task queue
celery -A app.worker.celery inspect reserved

# View task statistics
celery -A app.worker.celery inspect stats
```

### Performance Tuning

- **Database Indexes**: Optimize vector search with HNSW indexes
- **Chunk Size**: Balance context quality vs. search precision
- **Embedding Batch Size**: Optimize memory usage during ingestion
- **Connection Pooling**: Configure database connection limits

## Troubleshooting

### Common Issues & Solutions

**Issue: "ModuleNotFoundError: No module named 'app.core'"**
```bash
# Solution: Use module execution for tests
python -m pytest instead of pytest
```

**Issue: "Invalid or missing API Key"**
```bash
# Solution: Check X-API-KEY header in requests
curl -H "X-API-KEY: your-key" http://localhost:8000/health
```

**Issue: "Connection refused to PostgreSQL"**
```bash
# Solution: Verify services are running
docker-compose ps
docker-compose logs db
```

**Issue: "Celery worker not processing tasks"**
```bash
# Solution: Check worker status and logs
docker-compose logs worker
celery -A app.worker.celery inspect active
```

### Debugging Tips

1. **Check Service Health**: Use `/health` endpoint for diagnostics
2. **Monitor Resource Usage**: Watch CPU/memory during document processing
3. **Validate Environment**: Ensure all required environment variables are set

### Log Analysis

Key log patterns to monitor:

```bash
# Successful document processing
grep "Document processing completed" app.log

# API errors
grep "ERROR" app.log | grep "api"

# Database connection issues
grep "database" app.log | grep -i "error"

# Rate limiting events
grep "Rate limit exceeded" app.log
```

### FAQ

**Q: How large can uploaded ZIP files be?**
A: There is currently no max size

**Q: What document formats are supported?**
A: MD formats within ZIP archives.

**Q: How do I backup the vector database?**
A: Use PostgreSQL backup tools: `pg_dump docuquery_db > backup.sql`

**Q: Can I use a different embedding model?**
A: Yes, set `MODEL_NAME` in configuration to any sentence-transformers model.

**Q: How do I monitor API performance?**
A: Use the `/metrics` endpoint with Prometheus for comprehensive monitoring.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

We welcome contributions!

### Reporting Issues

Please use the [GitHub issue tracker](https://github.com/Igboke/DocuQuery-API/issues) to report bugs or request features.

## Support & Community

- **Documentation**: Comprehensive API docs available at `/docs` endpoint
- **Issues**: [GitHub Issues](https://github.com/Igboke/DocuQuery-API/issues)
- **Email**: For security issues, contact [danieligboke669@gmail.com]

---

**Built with**: FastAPI, PostgreSQL, Redis, Celery, OpenAI, Docker

**Maintained by**: [Igboke](https://github.com/Igboke)