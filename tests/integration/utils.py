from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


def load_cases(base_path, relative_path: str):
    base = Path(base_path)
    if base.suffix == ".py":
        base = base.parent
    return CaseLoader(base).load(relative_path)


def get_auth_client(base_client: ApiClient, token: Optional[str] = None) -> ApiClient:
    return ApiClient(base_url=base_client.base_url, timeout=base_client.timeout, token=token)


def extract_token(resp_json: dict) -> Optional[str]:
    return resp_json.get("token") or resp_json.get("data", {}).get("token")


def attach_case(step: str, resp: Any, payload: Any = None) -> None:
    attach_request_response({"step": step, "payload": payload}, resp)
