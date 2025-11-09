import asyncio
import httpx
import time
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
UPLOAD_ENDPOINT = "/api/v1/documents/upload"
STATUS_ENDPOINT = "/api/v1/documents/{job_id}/status"
FILE_TO_UPLOAD = "test_data/sample.zip"
API_KEY = os.getenv("API_KEY")

async def main():
    """
    Runs a full end-to-end test of the document upload and processing pipeline.
    """
    if not API_KEY:
        print("Error: API_KEY not found in environment. Please set it in your .env file.")
        return

    if not os.path.exists(FILE_TO_UPLOAD):
        print(f"Error: Test file not found at '{FILE_TO_UPLOAD}'")
        return
    
    headers = {"X-API-KEY": API_KEY}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0, headers=headers) as client:

        print(f"Uploading file: {FILE_TO_UPLOAD}...")
        with open(FILE_TO_UPLOAD, "rb") as f:
            files = {"file": (os.path.basename(FILE_TO_UPLOAD), f, "application/zip")}
            try:
                response = await client.post(UPLOAD_ENDPOINT, files=files)
                response.raise_for_status() 
            except httpx.RequestError as e:
                print(f"Error: Could not connect to the server at {BASE_URL}. Is it running?")
                return
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    print("Error: Got a 401 Unauthorized response. Is your API_KEY in .env correct?")
                else:
                    print(f"An HTTP error occurred: {e.response.status_code} - {e.response.text}")
                return

        if response.status_code == 202:
            job = response.json()
            job_id = job["job_id"]
            print(f"File accepted. Job ID: {job_id}")
        else:
            print(f"Upload failed with status {response.status_code}: {response.text}")
            return

        print("Polling for job completion...")
        start_time = time.time()
        while time.time() - start_time < 60:
            status_url = STATUS_ENDPOINT.format(job_id=job_id)
            status_response = await client.get(status_url)
            
            if status_response.status_code == 200:
                job_status = status_response.json()["status"]
                print(f"  Current status: {job_status}")
                if job_status in ["COMPLETED", "FAILED"]:
                    print(f"Job finished with status: {job_status}")
                    return
            else:
                print(f"  Error fetching status: {status_response.status_code}")

            await asyncio.sleep(2)

        print("Error: Job did not complete within the timeout period.")

if __name__ == "__main__":
    asyncio.run(main())