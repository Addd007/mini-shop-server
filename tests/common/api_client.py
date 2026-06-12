from __future__ import annotations

from typing import Any, Dict, Optional

import requests
from requests.auth import HTTPBasicAuth


class ApiClient:
    def __init__(self, base_url: str, timeout: int = 10, token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token = token
        self.session = requests.Session()

    def _request_kwargs(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        kwargs: Dict[str, Any] = {
            "headers": {"Accept": "application/json"},
        }
        if self.token:
            # 后端认证方式与 Postman 一致：Basic Auth，username 为 token，password 固定为 132
            kwargs["auth"] = HTTPBasicAuth(self.token, "132")
        if extra:
            kwargs["headers"].update(extra)
        return kwargs

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Any = None,
        files: Any = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> requests.Response:
        url = f"{self.base_url}{path if path.startswith('/') else '/' + path}"
        return self.session.request(
            method=method.upper(),
            url=url,
            params=params,
            json=json,
            data=data,
            files=files,
            timeout=self.timeout,
            **self._request_kwargs(headers),
        )
