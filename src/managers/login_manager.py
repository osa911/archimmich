from .api_manager import APIManager
from requests.exceptions import RequestException
from src.utils.helpers import save_settings

class LoginManager:
    def __init__(self, config=None):
        self.user = None
        self.api_manager = None
        self.config = config or {}

    def update_config(self, config: dict):
        """Update the configuration."""
        self.config = config or {}
        # If we have an active API manager, update its config too
        if self.api_manager:
            self.api_manager.update_config(self.config)

    def set_logger(self, logger):
        """Set the logger for this login manager and any existing API manager."""
        self.logger = logger
        if self.api_manager:
            self.api_manager.set_logger(logger)

    def set_credentials(self, server_ip: str, api_key: str, remember_me: bool):
        # Ensure the server_ip starts with 'http://' or 'https://'
        if not (server_ip.startswith("http://") or server_ip.startswith("https://")):
            server_ip = f"http://{server_ip}"

        # Remove trailing slashes and ensure `/api` is appended exactly once
        server_ip = server_ip.rstrip('/')
        if not server_ip.endswith("/api"):
            server_ip = f"{server_ip}/api"

        if remember_me:
            save_settings(server_ip, api_key)
        self.api_manager = APIManager(server_ip, api_key, config=self.config)

        # Set logger if we have one stored
        if hasattr(self, 'logger') and self.logger:
            self.api_manager.set_logger(self.logger)

    def getApiManager(self):
        return self.api_manager

    def login(self):
        if not self.api_manager:
            raise ValueError("API Manager not initialized with credentials.")
        try:
            self.user = self.api_manager.get("/users/me", expected_type=dict)
            return self.user
        except Exception as e:
            self.user = None
            raise

    def logout(self):
        self.user = None
        self.api_manager = None

    def is_logged_in(self):
        return self.user is not None

    def get_user(self):
        return self.user

    def get_avatar_fetcher(self):
        if not (self.user and "id" in self.user):
            from src.utils.helpers import render_default_avatar
            render_default_avatar(self)

        def fetch_avatar():
            try:
                # Note: For profile image, we want the raw response since it's binary data
                return self.api_manager.get(
                    f"/users/{self.user['id']}/profile-image",
                    expected_type=None
                )
            except RequestException as e:
                self.logs.append(f"Failed to load avatar: {str(e)}")
                raise e
        return fetch_avatar