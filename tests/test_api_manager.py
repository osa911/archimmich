import pytest
import requests
from src.managers.api_manager import APIManager

# Test Constants
API_HOST = "https://fake-api.com"
API_KEY = "test_api_key"


@pytest.fixture
def api_manager():
    """Fixture for APIManager instance."""
    return APIManager(api_host=API_HOST, api_key=API_KEY)


def test_get_headers(api_manager):
    """Test that get_headers returns the correct headers."""
    headers = api_manager.get_headers()
    assert headers == {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }


def test_get_success(requests_mock, api_manager):
    """Test GET request success."""
    endpoint = "/test-endpoint"
    test_response = {"message": "Success"}

    requests_mock.get(f"{API_HOST}{endpoint}", json=test_response, status_code=200)

    response = api_manager.get(endpoint)
    assert response.json() == test_response


def test_get_failure(requests_mock, api_manager):
    """Test GET request failure."""
    endpoint = "/test-error"

    requests_mock.get(f"{API_HOST}{endpoint}", status_code=404)

    with pytest.raises(requests.exceptions.HTTPError):
        api_manager.get(endpoint)


def test_post_success(requests_mock, api_manager):
    """Test POST request success."""
    endpoint = "/post-endpoint"
    payload = {"key": "value"}
    test_response = {"message": "Created"}

    requests_mock.post(f"{API_HOST}{endpoint}", json=test_response, status_code=201)

    response = api_manager.post(endpoint, json_data=payload)
    assert response.json() == test_response


def test_post_failure(requests_mock, api_manager):
    """Test POST request failure."""
    endpoint = "/post-error"
    payload = {"key": "value"}

    requests_mock.post(f"{API_HOST}{endpoint}", status_code=400)

    with pytest.raises(requests.exceptions.HTTPError):
        api_manager.post(endpoint, json_data=payload)