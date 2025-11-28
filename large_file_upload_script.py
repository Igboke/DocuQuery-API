"""
Test script to generate and upload a large markdown file in a ZIP archive to the DocuQuery API.
This tests the system's ability to handle large document uploads (target: ~400MB ZIP file).
"""

import asyncio
import httpx
import time
import os
import sys
import zipfile
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
UPLOAD_ENDPOINT = "/api/v1/documents/upload"
STATUS_ENDPOINT = "/api/v1/documents/{job_id}/status"
QUERY_ENDPOINT = "/api/v1/query"
API_KEY = os.getenv("API_KEY")

# Test configuration
# 50MB file will create ~29,000 chunks with 2000-char chunk size
# Processing time: ~20-25 minutes (58 batches × ~20-25 sec/batch)
TARGET_FILE_SIZE_MB = 50 
TEST_DATA_DIR = Path("test_data")
LARGE_FILE_PATH = TEST_DATA_DIR / "large_test_document.md"
LARGE_ZIP_PATH = TEST_DATA_DIR / "large_test_document.zip"


def generate_large_markdown_file(target_size_mb: int, output_path: Path):
    """
    Generate a large markdown file with realistic content.
    This file will be compressed into a ZIP archive for upload.
    
    Args:
        target_size_mb: Target size in megabytes (uncompressed)
        output_path: Path where the markdown file will be saved
    """
    print(f"Generating {target_size_mb}MB markdown file (uncompressed)...")
    
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    
    sample_sections = [
        """
# Introduction to Distributed Systems

Distributed systems are computing systems in which components located on networked computers 
communicate and coordinate their actions by passing messages. These systems are fundamental 
to modern cloud computing, web services, and large-scale applications.

## Key Characteristics

1. **Concurrency**: Multiple components execute simultaneously
2. **Lack of Global Clock**: No single global notion of correct time
3. **Independent Failures**: Components can fail independently
4. **Scalability**: Ability to handle growing amounts of work

## Common Challenges

### Network Partitions
Network partitions occur when network failures prevent some nodes from communicating with others.
This is a critical consideration in distributed system design, as outlined by the CAP theorem.

### Consistency Models
- Strong Consistency
- Eventual Consistency
- Causal Consistency
- Sequential Consistency

### Data Replication Strategies
Replication is essential for fault tolerance and performance. Common strategies include:
- Master-Slave Replication
- Multi-Master Replication
- Quorum-based Replication

""",
        """
# Database Architecture Patterns

Modern database systems employ various architectural patterns to achieve scalability, 
reliability, and performance. Understanding these patterns is crucial for building 
robust data-intensive applications.

## Relational Database Management Systems (RDBMS)

### ACID Properties
- **Atomicity**: Transactions are all-or-nothing
- **Consistency**: Database remains in valid state
- **Isolation**: Concurrent transactions don't interfere
- **Durability**: Committed data persists

### Normalization
Database normalization is the process of organizing data to reduce redundancy:
- First Normal Form (1NF)
- Second Normal Form (2NF)
- Third Normal Form (3NF)
- Boyce-Codd Normal Form (BCNF)

## NoSQL Databases

### Document Stores
Examples: MongoDB, CouchDB
Store data as JSON-like documents with flexible schemas.

### Key-Value Stores
Examples: Redis, DynamoDB
Simple key-value pairs for high-performance lookups.

### Column-Family Stores
Examples: Cassandra, HBase
Optimized for write-heavy workloads and wide-column data.

### Graph Databases
Examples: Neo4j, Amazon Neptune
Specialized for relationship-heavy data and graph queries.

""",
        """
# API Design Best Practices

Application Programming Interfaces (APIs) are the backbone of modern software integration.
Well-designed APIs are intuitive, scalable, and maintainable.

## RESTful API Principles

### Resource-Based URLs
URLs should represent resources, not actions:
- Good: `/api/v1/users/123`
- Bad: `/api/v1/getUser?id=123`

### HTTP Methods
- **GET**: Retrieve resources
- **POST**: Create new resources
- **PUT**: Update entire resources
- **PATCH**: Partial updates
- **DELETE**: Remove resources

### Status Codes
Proper use of HTTP status codes:
- 200 OK: Successful GET, PUT, PATCH
- 201 Created: Successful POST
- 204 No Content: Successful DELETE
- 400 Bad Request: Client error
- 401 Unauthorized: Authentication required
- 403 Forbidden: Authenticated but not authorized
- 404 Not Found: Resource doesn't exist
- 500 Internal Server Error: Server-side error

## Versioning Strategies

### URL Versioning
Include version in the URL path: `/api/v1/resources`

### Header Versioning
Use custom headers: `Accept: application/vnd.api+json;version=1`

### Query Parameter Versioning
Include version as parameter: `/api/resources?version=1`

## Authentication and Security

### API Key Authentication
Simple but limited security mechanism for identifying API consumers.

### OAuth 2.0
Industry-standard protocol for authorization, supporting multiple grant types.

### JWT (JSON Web Tokens)
Stateless authentication mechanism with encoded claims.

## Rate Limiting
Protect your API from abuse:
- Per-user limits
- Per-IP limits
- Time-based windows
- Token bucket algorithm

""",
        """
# Microservices Architecture

Microservices architecture structures applications as collections of loosely coupled, 
independently deployable services. Each service is focused on a specific business capability.

## Core Principles

### Single Responsibility
Each microservice should have one reason to change and handle one business capability.

### Decentralized Data Management
Each service manages its own database, avoiding shared databases that create coupling.

### Independent Deployment
Services can be deployed independently without affecting others.

### Fault Isolation
Failures in one service shouldn't cascade to others.

## Service Communication Patterns

### Synchronous Communication
- REST over HTTP/HTTPS
- gRPC for high-performance RPC
- GraphQL for flexible querying

### Asynchronous Communication
- Message Queues (RabbitMQ, Apache Kafka)
- Event-driven architecture
- Publish-Subscribe patterns

## Service Discovery

### Client-Side Discovery
Clients query a service registry to find available instances.

### Server-Side Discovery
Load balancer queries the service registry and routes requests.

## API Gateway Pattern
Centralized entry point for all client requests:
- Request routing
- Authentication and authorization
- Rate limiting
- Request/response transformation
- Monitoring and logging

## Circuit Breaker Pattern
Prevent cascading failures:
- Closed: Normal operation
- Open: Requests fail immediately
- Half-Open: Test if service recovered

""",
        """
# Cloud Computing Fundamentals

Cloud computing provides on-demand access to computing resources over the internet,
enabling scalability, flexibility, and cost optimization.

## Service Models

### Infrastructure as a Service (IaaS)
Virtualized computing resources over the internet.
Examples: AWS EC2, Google Compute Engine, Azure Virtual Machines

### Platform as a Service (PaaS)
Complete development and deployment environment in the cloud.
Examples: Heroku, Google App Engine, AWS Elastic Beanstalk

### Software as a Service (SaaS)
Software applications delivered over the internet.
Examples: Salesforce, Google Workspace, Microsoft 365

## Deployment Models

### Public Cloud
Services offered over the public internet and shared across organizations.

### Private Cloud
Cloud infrastructure operated solely for a single organization.

### Hybrid Cloud
Combination of public and private clouds with data and application portability.

### Multi-Cloud
Use of multiple cloud computing services from different providers.

## Key Services

### Compute Services
- Virtual Machines
- Container Services (ECS, Kubernetes)
- Serverless Functions (Lambda, Cloud Functions)

### Storage Services
- Object Storage (S3, Cloud Storage)
- Block Storage (EBS, Persistent Disk)
- File Storage (EFS, Filestore)

### Database Services
- Relational (RDS, Cloud SQL)
- NoSQL (DynamoDB, Firestore)
- Data Warehousing (Redshift, BigQuery)

### Networking Services
- Virtual Private Cloud (VPC)
- Load Balancers
- Content Delivery Networks (CDN)
- DNS Management

## Cost Optimization Strategies

### Right-Sizing
Match instance types to actual workload requirements.

### Reserved Instances
Commit to long-term usage for discounted rates.

### Spot Instances
Use spare capacity at reduced rates for fault-tolerant workloads.

### Auto-Scaling
Automatically adjust resources based on demand.

"""
    ]
    
    target_size_bytes = target_size_mb * 1024 * 1024
    current_size = 0
    section_index = 0
    
    with open(output_path, 'w', encoding='utf-8') as f:
        header = f"# Large Test Document ({target_size_mb}MB Uncompressed)\n\n"
        header += "This is a generated test document to verify the DocuQuery API's ability to handle large ZIP files.\n"
        header += "The document will be compressed into a ZIP archive before upload.\n\n"
        f.write(header)
        current_size += len(header.encode('utf-8'))
        
        iteration = 0
        while current_size < target_size_bytes:
            if iteration % 100 == 0:
                marker = f"\n## Section Group {iteration // 100}\n\n"
                f.write(marker)
                current_size += len(marker.encode('utf-8'))
            
            section = sample_sections[section_index]
            f.write(section)
            current_size += len(section.encode('utf-8'))
            
            section_index = (section_index + 1) % len(sample_sections)
            iteration += 1
            
            if iteration % 1000 == 0:
                progress_mb = current_size / (1024 * 1024)
                print(f"  Progress: {progress_mb:.1f}MB / {target_size_mb}MB")
    
    final_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"✓ Generated file: {output_path}")
    print(f"✓ File size: {final_size_mb:.2f}MB")
    return output_path


def create_zip_file(markdown_path: Path, zip_path: Path):
    """
    Create a ZIP file containing the markdown document.
    
    Args:
        markdown_path: Path to the markdown file to compress
        zip_path: Path where the ZIP file will be saved
    """
    print(f"\nCreating ZIP archive...")
    
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        zipf.write(markdown_path, markdown_path.name)
    
    zip_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    md_size_mb = os.path.getsize(markdown_path) / (1024 * 1024)
    compression_ratio = (1 - zip_size_mb / md_size_mb) * 100
    
    print(f"✓ Created ZIP file: {zip_path}")
    print(f"✓ ZIP size: {zip_size_mb:.2f}MB")
    print(f"✓ Compression ratio: {compression_ratio:.1f}%")
    
    return zip_path


async def upload_file(file_path: Path, client: httpx.AsyncClient):
    """Upload a file to the API and return the job ID."""
    print(f"\nUploading file: {file_path.name}...")
    print(f"File size: {os.path.getsize(file_path) / (1024 * 1024):.2f}MB")
    
    with open(file_path, "rb") as f:
        files = {"file": (file_path.name, f, "application/zip")}
        
        try:
            response = await client.post(UPLOAD_ENDPOINT, files=files, timeout=300.0)
            response.raise_for_status()
        except httpx.RequestError as e:
            print(f"✗ Error: Could not connect to the server at {BASE_URL}. Is it running?")
            print(f"  Details: {e}")
            return None
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print("✗ Error: Got a 401 Unauthorized response. Is your API_KEY in .env correct?")
            elif e.response.status_code == 400:
                print(f"✗ Error: Bad request - {e.response.text}")
            else:
                print(f"✗ An HTTP error occurred: {e.response.status_code} - {e.response.text}")
            return None
    
    if response.status_code == 202:
        job = response.json()
        job_id = job["job_id"]
        print(f"✓ File accepted. Job ID: {job_id}")
        return job_id
    else:
        print(f"✗ Upload failed with status {response.status_code}: {response.text}")
        return None


async def poll_job_status(job_id: str, client: httpx.AsyncClient, timeout: int = 300):
    """Poll the job status until completion or timeout."""
    print(f"\nPolling for job completion (timeout: {timeout}s)...")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout:
        status_url = STATUS_ENDPOINT.format(job_id=job_id)
        
        try:
            status_response = await client.get(status_url)
            status_response.raise_for_status()
        except Exception as e:
            print(f"  Error fetching status: {e}")
            await asyncio.sleep(5)
            continue
        
        if status_response.status_code == 200:
            job_data = status_response.json()
            job_status = job_data["status"]
            
            if job_status != last_status:
                elapsed = time.time() - start_time
                print(f"  [{elapsed:.1f}s] Status: {job_status}")
                last_status = job_status
            
            if job_status == "COMPLETED":
                print(f"✓ Job completed successfully!")
                return True
            elif job_status == "FAILED":
                print(f"✗ Job failed.")
                return False
        
        await asyncio.sleep(5)
    
    print(f"✗ Error: Job did not complete within {timeout}s timeout.")
    return False


async def test_query(client: httpx.AsyncClient, question: str):
    """Test querying the knowledge base."""
    print(f"\nTesting query: '{question}'")
    
    try:
        response = await client.post(
            QUERY_ENDPOINT,
            json={"question": question},
            timeout=60.0
        )
        response.raise_for_status()
        
        result = response.json()
        print(f"✓ Query successful!")
        print(f"  Answer: {result['answer'][:200]}...")
        print(f"  Sources: {len(result['sources'])} chunks")
        return True
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False


async def main():
    """Main test orchestration."""
    print("=" * 70)
    print("Large File Upload Test for DocuQuery API")
    print("=" * 70)
    
    if not API_KEY:
        print("✗ Error: API_KEY not found in environment. Please set it in your .env file.")
        return 1
    
    print(f"\n[Step 1] Generating {TARGET_FILE_SIZE_MB}MB markdown file...")
    try:
        md_path = generate_large_markdown_file(TARGET_FILE_SIZE_MB, LARGE_FILE_PATH)
    except Exception as e:
        print(f"✗ Error generating markdown file: {e}")
        return 1
    
    print(f"\n[Step 2] Creating ZIP archive...")
    try:
        zip_path = create_zip_file(md_path, LARGE_ZIP_PATH)
    except Exception as e:
        print(f"✗ Error creating ZIP file: {e}")
        return 1
    
    print(f"\n[Step 3] Uploading ZIP file to API...")
    headers = {"X-API-KEY": API_KEY}
    
    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers) as client:
        job_id = await upload_file(zip_path, client)
        
        if not job_id:
            print("\n✗ Test FAILED: Could not upload file")
            return 1
        
        print(f"\n[Step 4] Monitoring document processing...")
        success = await poll_job_status(job_id, client, timeout=1800)  # 30 minute timeout for 50MB
        
        if not success:
            print("\n✗ Test FAILED: Document processing failed or timed out")
            return 1
        
        print(f"\n[Step 5] Testing query capabilities...")
        query_success = await test_query(
            client,
            "What are the key characteristics of distributed systems?"
        )
        
        if not query_success:
            print("\n⚠ Warning: Document processed but query failed")
            return 1
    
    # Success!
    zip_size_mb = os.path.getsize(LARGE_ZIP_PATH) / (1024 * 1024)
    print("\n" + "=" * 70)
    print("✓ ALL TESTS PASSED!")
    print(f"✓ Successfully uploaded and processed a {zip_size_mb:.2f}MB ZIP file")
    print(f"✓ Containing {TARGET_FILE_SIZE_MB}MB of markdown content")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
