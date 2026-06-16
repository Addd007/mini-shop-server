"""
订单接口自动化测试

测试依据：test_cases/1号/order.md
数据来源：tests/cases/1号/order_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化测试数据

测试分组：
  - order_place  : 订单提交
  - order_list   : 订单列表
  - order_detail : 订单详情

运行方式：
  pytest tests/api/1号/test_order_cases.py -v
  pytest tests/api/1号/test_order_cases.py -k TC-ORDER-001
  pytest -m order -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import subprocess
import sys

import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


CASE_FILE = "cases/1号/order_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [case for case in cases if case.get("tag") == tag]


def _extract_token(resp_json: dict) -> str | None:
    return resp_json.get("token") or resp_json.get("data", {}).get("token")


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


@pytest.fixture(scope="session", autouse=True)
def initialize_test_data():
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[3] / "fake.py"), "--scope", "users"],
        check=True,
    )


ALL_CASES = _load_cases()
ORDER_PLACE_CASES = _filter_by_tag(ALL_CASES, "order_place")
ORDER_LIST_CASES = _filter_by_tag(ALL_CASES, "order_list")
ORDER_DETAIL_CASES = _filter_by_tag(ALL_CASES, "order_detail")


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    accounts = [
        ("super", "super", "123456"),
        ("admin", "admin", "123456"),
        ("user", "user", "123456"),
    ]
    result: Dict[str, str] = {}
    for name, account, secret in accounts:
        resp = client.request("POST", "/v1/token", json={"account": account, "secret": secret, "type": 100})
        token = _extract_token(resp.json())
        if token:
            result[name] = token
    return result


def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    if auth == "none" or not auth:
        return ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    return ApiClient(base_url=client.base_url, timeout=client.timeout, token=tokens.get(auth))


def _execute_case(client: ApiClient, tokens: Dict[str, str], case: dict) -> Any:
    auth_client = _get_auth_client(client, tokens, case.get("auth", "none"))
    return auth_client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/v1/order"),
        json=case.get("json") if case.get("json") else None,
        params=case.get("params"),
        headers=case.get("headers"),
    )


def _assert_error_response(case: dict, resp, body: dict):
    if resp.status_code == 200:
        assert _has_error(body), f"[{case['id']}] 业务应返回非零 error_code: {body}"
    else:
        assert resp.status_code in (400, 401, 403, 404, 422, 500), (
            f"[{case['id']}] 期望 4xx/5xx, 实际 {resp.status_code}"
        )


@pytest.mark.order
@pytest.mark.parametrize("case", ORDER_PLACE_CASES, ids=[c["id"] for c in ORDER_PLACE_CASES])
def test_order_place(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
        )
    if expected.get("error"):
        _assert_error_response(case, resp, body)


@pytest.mark.order
@pytest.mark.parametrize("case", ORDER_LIST_CASES, ids=[c["id"] for c in ORDER_LIST_CASES])
def test_order_list(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
        )
    if expected.get("error"):
        _assert_error_response(case, resp, body)


@pytest.mark.order
@pytest.mark.parametrize("case", ORDER_DETAIL_CASES, ids=[c["id"] for c in ORDER_DETAIL_CASES])
def test_order_detail(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
        )
    if expected.get("error"):
        _assert_error_response(case, resp, body)
