import requests
from typing import Optional, Any, Dict
from src.utils.helpers import Logger

class APIError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(self.message)

class APIManager:
    def __init__(self, server_url, api_key, config=None, logger=None):
        self.server_url = server_url
        self.api_key = api_key
        self.logger = logger
        self.config = config or {}
        self.debug = self.config.get('debug', {
            'verbose_logging': False,
            'log_api_requests': False,
            'log_api_responses': False,
            'log_request_bodies': False
        })
        self.server_info = None

    def set_logger(self, logger: Logger):
        self.logger = logger

    def log(self, message: str, force: bool = False):
        if self.logger and (force or self.debug.get('verbose_logging', False)):
            self.logger.append(message)

    def get_headers(self) -> Dict[str, str]:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

    def _handle_response(self, response: requests.Response, expected_type: Optional[type] = None) -> Any:
        try:
            # For binary responses or when no type validation is needed
            if expected_type is None:
                response.raise_for_status()
                return response

            # Try to parse response as JSON first to check for API errors
            try:
                error_json = response.json()
                # Check if this is an Immich error response
                if not response.ok and isinstance(error_json, dict) and 'message' in error_json:
                    error_msg = f"API Error: {error_json.get('message')} (Status: {error_json.get('statusCode')}, Error: {error_json.get('error')})"
                    # self.log(error_msg)
                    raise APIError(error_msg, response.status_code, response.text)
            except requests.exceptions.JSONDecodeError:
                # Not a JSON response or not an error response format we recognize
                pass

            response.raise_for_status()

            # For streaming responses that don't need JSON parsing, return as is
            if response.headers.get('Transfer-Encoding') == 'chunked' and expected_type is None:
                return response

            # Parse response as JSON
            try:
                data = response.json()
            except requests.exceptions.JSONDecodeError as e:
                self.log(f"Failed to parse JSON response: {str(e)}")
                self.log(f"Raw response text: {response.text}")
                raise

            # Validate response type if expected_type is provided
            if expected_type and not isinstance(data, expected_type):
                error_msg = f"Unexpected response format. Expected {expected_type.__name__} but got {type(data).__name__}"
                self.log(error_msg)
                self.log(f"Response data: {data}")
                raise APIError(error_msg, response.status_code, response.text)

            return data

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error: {str(e)}"
            self.log(error_msg)
            try:
                error_json = response.json()
                if isinstance(error_json, dict) and 'message' in error_json:
                    error_msg = f"API Error: {error_json.get('message')} (Status: {error_json.get('statusCode')}, Error: {error_json.get('error')}, CorrelationId: {error_json.get('correlationId')})"
                    self.log(error_msg)
            except:
                self.log(f"Error response body: {response.text}")
            raise APIError(error_msg, response.status_code, response.text)

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.log(error_msg)
            try:
                self.log(f"Response body: {response.text}")
            except:
                self.log("Could not access response body")
            raise APIError(error_msg, getattr(response, 'status_code', None), getattr(response, 'text', None))

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make an HTTP request to the API."""
        url = f"{self.server_url}{endpoint}"

        if self.debug.get('log_api_requests', False):
            self.log(f"Making {method} request to: {url}")
            self.log(f"Request headers: {self.get_headers()}")

        if kwargs.get('json_data') and self.debug.get('log_request_bodies', False):
            self.log(f"Request body: {kwargs['json_data']}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.get_headers(),
                json=kwargs.get('json_data'),
                stream=kwargs.get('stream', False)
            )

            if self.debug.get('log_api_responses', False):
                if not kwargs.get('stream'):
                    try:
                        self.log(f"Response status: {response.status_code}")
                        self.log(f"Response body: {response.text[:1000]}...")
                    except:
                        self.log("Could not log response body")
                else:
                    self.log(f"Streaming response started with status: {response.status_code}")

            return response

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.log(error_msg, force=True)  # Always log errors
            raise

    def get(self, endpoint: str, expected_type: Optional[type] = None) -> Any:
        """Make a GET request to the API."""
        response = self._make_request('GET', endpoint)
        return self._handle_response(response, expected_type)

    def post(self, endpoint: str, json_data: Optional[dict] = None, stream: bool = False, expected_type: Optional[type] = None) -> Any:
        """Make a POST request to the API."""
        response = self._make_request('POST', endpoint, json_data=json_data, stream=stream)
        return self._handle_response(response, expected_type)

    def get_server_info(self) -> dict:
        """Fetch server version information."""
        if not self.server_info:
            self.server_info = self.get('/server/about', dict)
            if self.server_info:
                self.log(f"Connected to Immich server version {self.server_info.get('version', 'unknown')}", force=True)
        return self.server_info