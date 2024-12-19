import requests

class APIManager:
    def __init__(self, api_host: str, api_key: str):
        self.api_host = api_host
        self.api_key = api_key

    def get_headers(self):
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, **kwargs):
        url = f"{self.api_host}{endpoint}"
        response = requests.get(url, headers=self.get_headers(), **kwargs)
        response.raise_for_status()
        return response

    def post(self, endpoint: str, json_data=None, **kwargs):
        url = f"{self.api_host}{endpoint}"
        response = requests.post(url, headers=self.get_headers(), json=json_data, **kwargs)
        response.raise_for_status()
        return response