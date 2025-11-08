import os
import zipfile
import textwrap

OUTPUT_DIR = "test_data"
ZIP_FILENAME = "sample.zip"
FILES_TO_CREATE = {
    "auth_service.md": """
    # Authentication Service Documentation

    ## Overview
    The Authentication Service is responsible for user login, registration, and token management.
    It uses JWT for secure token generation.

    ## Retry Logic
    When an external provider fails, the system should retry the connection up to 3 times
    with an exponential backoff strategy. The initial delay is 100ms.
    """,
    "api_gateway.md": """
    # API Gateway

    ## Routing
    The gateway routes incoming traffic based on the request path.
    - `/api/v1/query` is routed to the Query Service.
    - `/api/v1/documents` is routed to the Ingestion Service.

    All routes are protected by an API Key authentication scheme.
    """,
    "database_schema.md": """
    # Database Schema

    ## Tables
    - **documents**: Tracks the status of ingested files.
    - **chunks**: Stores the vector data and text snippets.

    The `chunks` table has an HNSW index on the `embedding` column to ensure
    fast similarity searches. This is critical for performance.
    """,
    "deployment.txt": """
    This is a text file, not a markdown file.
    The ingestion pipeline should ignore this file.
    """
}

def create_test_zip():
    """
    Creates a directory with sample markdown files and zips them up.
    """

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Directory '{OUTPUT_DIR}' ensured.")

    file_paths = []
    for filename, content in FILES_TO_CREATE.items():
        file_path = os.path.join(OUTPUT_DIR, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(textwrap.dedent(content).strip())
        file_paths.append(file_path)
        print(f"  - Created file: {filename}")

    zip_path = os.path.join(OUTPUT_DIR, ZIP_FILENAME)
    print(f"\nCreating zip file: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for file_path in file_paths:
            arcname = os.path.basename(file_path)
            zipf.write(file_path, arcname=arcname)
            print(f"  - Added {arcname} to zip.")

    print("\nCleaning up individual files...")
    for file_path in file_paths:
        os.remove(file_path)
    
    print(f"\nSuccessfully created '{zip_path}' with {len(FILES_TO_CREATE)} files inside.")

if __name__ == "__main__":
    create_test_zip()