from typing import Any
from httpx import Client
import pytest


class TestQueryEndpoint:
    """
    A test class to group all tests related to the /query endpoint.
    """

    def test_query_happy_path(self, test_client_sync: Client):
        """
        Tests a successful query with a valid question.
        Expects a 200 OK response with the correct structure.
        """

        request_data = {"question": "How does the retry logic work?"}

        response = test_client_sync.post("/api/v1/query", json=request_data)

        assert response.status_code == 200
        
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert isinstance(data["sources"], list)
        assert "placeholder answer" in data["answer"]

    @pytest.mark.parametrize(
        "invalid_payload, expected_detail_part",
        [
            ({}, "Field required"),
            ({"question": None}, "Input should be a valid string"),
            ({"question": ""}, "String should have at least 3 characters"),
            ({"question": "hi"}, "String should have at least 3 characters"),
            ({"question": 123}, "Input should be a valid string"),
        ]
    )
    def test_query_validation_errors(
        self, test_client_sync: Client, invalid_payload: dict[Any, Any], expected_detail_part: str
    ):
        """
        Tests various invalid request payloads.
        Expects a 422 Unprocessable Entity response with a helpful error message.
        """
        response = test_client_sync.post("/api/v1/query", json=invalid_payload)

        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
        assert any(expected_detail_part in detail["msg"] for detail in error_data["detail"])