from typing import Optional

from tests.common.api_client import ApiClient


class TokenManager:
    def __init__(self, base_url: str, timeout: int = 10):
        self.client = ApiClient(base_url, timeout=timeout)
        self._token: Optional[str] = None

    @property
    def token(self) -> Optional[str]:
        return self._token

    def set_token(self, token: str) -> None:
        self._token = token
        self.client.token = token

    def clear(self) -> None:
        self._token = None
        self.client.token = None

    def login(self, username: str, password: str) -> str:
        response = self.client.request(
            "POST",
            "/v1/token",
            json={"username": username, "password": password},
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("token") or payload.get("data", {}).get("token")
        if not token:
            raise ValueError("Login response does not contain token")
        self.set_token(token)
        return token
