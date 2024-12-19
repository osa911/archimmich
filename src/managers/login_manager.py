from .api_manager import APIManager
from requests.exceptions import RequestException

class LoginManager:
    def __init__(self):
        self.user = None
        self.api_manager = None

    def set_credentials(self, server_ip: str, api_key: str):
        # Ensure the server_ip starts with 'http://' or 'https://'
        if not (server_ip.startswith("http://") or server_ip.startswith("https://")):
            server_ip = f"http://{server_ip}"

        # Ensure `/api` is appended to the host if not present
        if not server_ip.endswith("/api"):
            server_ip = f"{server_ip}/api"

        self.api_manager = APIManager(server_ip, api_key)

    def getApiManager(self):
        return self.api_manager

    def login(self):
        if not self.api_manager:
            raise ValueError("API Manager not initialized with credentials.")
        response = self.api_manager.get("/users/me")
        self.user = response.json()
        return self.user

    def logout(self):
        self.user = None
        self.api_manager = None

    def is_logged_in(self):
        return self.user is not None

    def get_user(self):
        return self.user

    def get_avatar_fetcher(self):
        # if self.user and "id" in self.user:
        #     def fetch_avatar():
        #         try:
        #             return self.api_manager.get(f"/users/{self.user['id']}/profile-image")
        #         except RequestException as e:
        #             self.logs.append(f"Failed to load avatar: {str(e)}")
        #             raise e
        #     return fetch_avatar
        # return None

        if not (self.user and "id" in self.user):
            from src.utils.helpers import render_default_avatar
            render_default_avatar(self)

        def fetch_avatar():
            try:
                return self.api_manager.get(f"/users/{self.user['id']}/profile-image")
            except RequestException as e:
                self.logs.append(f"Failed to load avatar: {str(e)}")
                raise e
        return fetch_avatar