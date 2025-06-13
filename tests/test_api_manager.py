import pytest
from src.managers.api_manager import APIManager, APIError

# Test Constants
API_HOST = "https://fake-api.com"
API_KEY = "test-key"


@pytest.fixture
def api_manager():
    """Fixture for APIManager instance."""
    return APIManager(server_url=API_HOST, api_key=API_KEY)


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

    with pytest.raises(APIError):
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

    with pytest.raises(APIError):
        api_manager.post(endpoint, json_data=payload)


def test_get_server_info_success(requests_mock, api_manager):
    """Test successful server info retrieval."""
    mock_response = {
        "version": "v1.134.0",
        "buildImage": "v1.134.0",
        "build": "15281783550"
    }
    requests_mock.get(f"{API_HOST}/server/about", json=mock_response)

    # First call should make the request
    result = api_manager.get_server_info()
    assert result == mock_response
    assert requests_mock.call_count == 1

    # Second call should use cached value
    result = api_manager.get_server_info()
    assert result == mock_response
    assert requests_mock.call_count == 1  # Call count shouldn't increase


def test_get_server_info_failure(requests_mock, api_manager):
    """Test server info retrieval failure."""
    requests_mock.get(f"{API_HOST}/server/about", status_code=500)

    with pytest.raises(APIError):
        api_manager.get_server_info()