"""
路由管理自动化测试

测试依据：test_cases/2号/route.md
数据来源：tests/cases/2号/route_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化用户测试数据

测试分组（按 YAML 中的 tag 字段划分）：
  - route_tree              : 路由树查询（TC-ROUTE-001 ~ 002）
  - route_node              : 路由节点查询（TC-ROUTE-003）
  - route_create            : 新增节点（TC-ROUTE-004）
  - route_create_validation : 新增异常校验（TC-ROUTE-005）
  - route_update            : 修改节点（TC-ROUTE-006）
  - route_delete            : 删除节点（TC-ROUTE-007）
  - route_access_control    : 越权 + 未登录（TC-ROUTE-008 ~ 009）

运行方式：
  pytest tests/api/2号/test_route_cases.py -v
  pytest tests/api/2号/test_route_cases.py -k TC-ROUTE-001
  pytest -m route -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.auth_seed import get_test_tokens
from tests.common.case_loader import CaseLoader


CASE_FILE = "cases/2号/route_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [c for c in cases if c.get("tag") == tag]


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0



def _skip_if_marked(case: dict):
    """如果用例标记了 skip: true，则跳过该用例。"""
    if case.get("skip"):
        pytest.skip(case.get("skip_reason", "用例已标记跳过"))

ALL_CASES = _load_cases()
ROUTE_TREE_CASES = _filter_by_tag(ALL_CASES, "route_tree")
ROUTE_NODE_CASES = _filter_by_tag(ALL_CASES, "route_node")
ROUTE_CREATE_CASES = _filter_by_tag(ALL_CASES, "route_create")
ROUTE_CREATE_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "route_create_validation")
ROUTE_UPDATE_CASES = _filter_by_tag(ALL_CASES, "route_update")
ROUTE_DELETE_CASES = _filter_by_tag(ALL_CASES, "route_delete")
ROUTE_ACCESS_CONTROL_CASES = _filter_by_tag(ALL_CASES, "route_access_control")


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    return get_test_tokens(client)


def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    if auth == "none" or not auth:
        return ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    token = tokens.get(auth)
    return ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)


def _execute_case(client: ApiClient, tokens: Dict[str, str], case: dict) -> Any:
    auth = case.get("auth", "none")
    auth_client = _get_auth_client(client, tokens, auth)
    return auth_client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/cms/route/tree"),
        json=case.get("json") if case.get("json") else None,
        headers=case.get("headers"),
        params=case.get("params"),
    )


def _assert_error_response(case: dict, resp, body: dict):
    if resp.status_code == 200:
        assert _has_error(body), f"[{case['id']}] 业务应返回非零 error_code: {body}"
    else:
        assert resp.status_code in (400, 401, 403, 404, 422, 500), (
            f"[{case['id']}] 期望 4xx/5xx, 实际 {resp.status_code}"
        )


def _run_case(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"路由管理 - {case['id']}")
    allure.dynamic.feature("路由管理")
    allure.dynamic.story(case.get("tag", "路由用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


# ===========================================================================
# 路由树查询 (TC-ROUTE-001 ~ TC-ROUTE-002)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_TREE_CASES, ids=[c["id"] for c in ROUTE_TREE_CASES])
def test_route_tree(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 路由节点查询 (TC-ROUTE-003)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_NODE_CASES, ids=[c["id"] for c in ROUTE_NODE_CASES])
def test_route_node(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 新增节点 (TC-ROUTE-004)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_CREATE_CASES, ids=[c["id"] for c in ROUTE_CREATE_CASES])
def test_route_create(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 新增异常校验 (TC-ROUTE-005)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_CREATE_VALIDATION_CASES, ids=[c["id"] for c in ROUTE_CREATE_VALIDATION_CASES])
def test_route_create_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    with allure.step("校验错误响应"):
        _assert_error_response(case, resp, body)


# ===========================================================================
# 修改节点 (TC-ROUTE-006)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_UPDATE_CASES, ids=[c["id"] for c in ROUTE_UPDATE_CASES])
def test_route_update(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 删除节点 (TC-ROUTE-007)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_DELETE_CASES, ids=[c["id"] for c in ROUTE_DELETE_CASES])
def test_route_delete(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 越权 + 未登录 (TC-ROUTE-008 ~ TC-ROUTE-009)
# ===========================================================================

@pytest.mark.route
@pytest.mark.parametrize("case", ROUTE_ACCESS_CONTROL_CASES, ids=[c["id"] for c in ROUTE_ACCESS_CONTROL_CASES])
def test_route_access_control(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    with allure.step("校验错误响应"):
        _assert_error_response(case, resp, body)
