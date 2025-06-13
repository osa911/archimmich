import pytest
from unittest.mock import MagicMock, patch
from src.managers.login_manager import LoginManager
from src.managers.api_manager import APIManager


@pytest.fixture
def login_manager():
    """Fixture to create a LoginManager instance."""
    return LoginManager()


# Test set_credentials
def test_set_credentials_with_valid_input(login_manager):
    """Test if credentials are set correctly."""
    with patch('src.managers.login_manager.save_settings') as mock_save_settings:
        with patch('src.managers.login_manager.APIManager') as MockAPIManager:
            mock_api_manager_instance = MockAPIManager.return_value

            # Call the set_credentials method
            login_manager.set_credentials("http://localhost", "test_api_key", remember_me=True)

            # Ensure APIManager was instantiated with correct parameters
            MockAPIManager.assert_called_once_with("http://localhost/api", "test_api_key", config={})

            # Ensure settings were saved
            mock_save_settings.assert_called_once_with("http://localhost/api", "test_api_key")

            # Ensure api_manager is assigned correctly
            assert login_manager.api_manager == mock_api_manager_instance

def test_set_credentials_without_protocol(login_manager):
    """Test if 'http://' is added when missing."""
    with patch('src.managers.login_manager.APIManager') as MockAPIManager:
        login_manager.set_credentials("localhost", "test_api_key", remember_me=False)

        # Ensure APIManager is called with the correct server IP
        MockAPIManager.assert_called_once_with("http://localhost/api", "test_api_key", config={})

def test_set_credentials_with_extra_slash(login_manager):
    """Ensure trailing slashes are handled correctly."""
    with patch('src.managers.login_manager.APIManager') as MockAPIManager:
        login_manager.set_credentials("http://localhost/api/", "test_api_key", remember_me=False)

        # Assert APIManager was initialized with the correct processed URL
        MockAPIManager.assert_called_once_with("http://localhost/api", "test_api_key", config={})

# Test getApiManager
def test_get_api_manager(login_manager):
    """Ensure API manager is returned."""
    login_manager.set_credentials("http://localhost", "test_api_key", remember_me=False)
    api_manager = login_manager.getApiManager()
    assert isinstance(api_manager, APIManager)


# Test login
def test_login_success(login_manager):
    """Test successful login."""
    with patch.object(APIManager, 'get') as mock_get:
        mock_response = {"id": "123", "name": "Test User"}
        mock_get.return_value = mock_response

        login_manager.set_credentials("http://localhost", "test_api_key", remember_me=False)
        user = login_manager.login()
        assert user['id'] == "123"
        assert user['name'] == "Test User"


def test_login_without_credentials(login_manager):
    """Ensure login raises error if credentials are missing."""
    with pytest.raises(ValueError):
        login_manager.login()


# Test logout
def test_logout(login_manager):
    """Ensure logout clears user and API manager."""
    login_manager.set_credentials("http://localhost", "test_api_key", remember_me=False)
    login_manager.login = MagicMock()
    login_manager.login()
    login_manager.logout()
    assert login_manager.user is None
    assert login_manager.api_manager is None


# Test is_logged_in
def test_is_logged_in(login_manager):
    """Test login status."""
    login_manager.user = {"id": "123"}
    assert login_manager.is_logged_in()

    login_manager.logout()
    assert not login_manager.is_logged_in()


# Test get_user
def test_get_user(login_manager):
    """Test retrieving user information."""
    login_manager.user = {"id": "123", "name": "Test User"}
    user = login_manager.get_user()
    assert user['id'] == "123"
    assert user['name'] == "Test User"


# Test get_avatar_fetcher
def test_get_avatar_fetcher(login_manager):
    """Test avatar fetcher."""
    login_manager.user = {"id": "123"}
    login_manager.set_credentials("http://localhost", "test_api_key", remember_me=False)
    with patch.object(APIManager, 'get') as mock_get:
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_get.return_value = mock_response

        fetch_avatar = login_manager.get_avatar_fetcher()
        response = fetch_avatar()
        assert response.content == b"fake_image_data"