from __future__ import annotations

from pathlib import Path
from typing import Optional

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.integration.utils import attach_case, extract_token, load_cases


CASES = load_cases(Path(__file__).resolve().parent, "auth_cases.yaml")


@pytest.fixture(scope="module", autouse=True)
def seed_auth_data(seed_users):
    yield


@pytest.fixture(scope="module")
def client(integration_client: ApiClient) -> ApiClient:
    return integration_client


@pytest.fixture(scope="module")
def valid_token(integration_tokens) -> str:
    token = integration_tokens.get("super")
    if not token:
        pytest.skip("无法获取有效 token，跳过 token 校验用例")
    return token


def _execute_case(client: ApiClient, case: dict, token: Optional[str] = None):
    json_body = case.get("json", {}).copy()
    if token and json_body.get("token") == "{valid_token}":
        json_body["token"] = token
    path = case.get("path", "/v1/token")
    if path.endswith("/verify") and token:
        verify_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)
        return verify_client.request(
            method=case.get("method", "POST"),
            path=path,
            json={"token": token},
            headers=case.get("headers"),
            params=case.get("params"),
        )
    return client.request(
        method=case.get("method", "POST"),
        path=path,
        json=json_body,
        headers=case.get("headers"),
        params=case.get("params"),
    )


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_auth_scenarios(client: ApiClient, case: dict, valid_token: str):
    allure.dynamic.title(f"鉴权场景 - {case['id']}")
    token = valid_token if case["id"] == "AUTH-SC-004" else None
    resp = _execute_case(client, case, token=token)
    body = resp.json()
    attach_case(case["id"], resp, case.get("json"))
    expected = case.get("expected", {})
    if expected.get("status_code"):
        assert resp.status_code == expected["status_code"]
    if expected.get("has_token") is True:
        assert extract_token(body)
    if expected.get("has_token") is False:
        assert not extract_token(body)
    if expected.get("json"):
        for key, value in expected["json"].items():
            assert body.get(key) == value