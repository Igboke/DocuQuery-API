import io
from httpx import AsyncClient
from pytest_mock import MockerFixture

async def test_upload_zip_file_success(test_client: AsyncClient):
    """
    Tests the successful upload of a .zip file.
    """
    zip_content = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    files = {"file": ("mydocs.zip", io.BytesIO(zip_content), "application/zip")}

    response = await test_client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 202
    
    data = response.json()
    assert data["filename"] == "mydocs.zip"
    assert data["status"] == "PENDING"
    assert "job_id" in data

async def test_upload_invalid_file_type(test_client: AsyncClient):
    """
    Tests that uploading a non-zip file results in a 400 error.
    """
    files = {"file": ("test.txt", io.BytesIO(b"some text"), "text/plain")}

    response = await test_client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    data = response.json()
    assert "Invalid file type" in data["detail"]


async def test_upload_enqueues_background_task(
    test_client: AsyncClient,
    mocker: MockerFixture
):
    """
    Tests that a successful upload correctly calls the background dispatcher task.
    """
    mock_dispatch = mocker.patch('app.services.document_service.dispatch_processing_task.delay')

    zip_content = b"PK\x05\x06\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    files = {"file": ("test_task.zip", io.BytesIO(zip_content), "application/zip")}

    response = await test_client.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 202
    
    job_id = response.json()["job_id"]

    mock_dispatch.assert_called_once_with(job_id)