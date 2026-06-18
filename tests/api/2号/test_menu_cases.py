"""
菜单管理自动化测试

测试依据：test_cases/2号/menu.md
数据来源：tests/cases/2号/menu_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化用户测试数据

测试分组（按 YAML 中的 tag 字段划分）：
  - menu_query              : 权限组菜单查询 + 不同组菜单对比（TC-MENU-001 ~ 002）
  - menu_query_validation   : 参数校验（TC-MENU-003）
  - menu_override           : 覆盖权限组菜单（TC-MENU-004）
  - menu_override_validation: 覆盖异常校验（TC-MENU-005）
  - menu_consistency        : 覆盖后一致性验证（TC-MENU-006）
  - menu_access_control     : 未登录（TC-MENU-007）

运行方式：
  pytest tests/api/2号/test_menu_cases.py -v
  pytest tests/api/2号/test_menu_cases.py -k TC-MENU-001
  pytest -m menu -v
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


CASE_FILE = "cases/2号/menu_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [c for c in cases if c.get("tag") == tag]


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


ALL_CASES = _load_cases()
MENU_QUERY_CASES = _filter_by_tag(ALL_CASES, "menu_query")
MENU_QUERY_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "menu_query_validation")
MENU_OVERRIDE_CASES = _filter_by_tag(ALL_CASES, "menu_override")
MENU_OVERRIDE_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "menu_override_validation")
MENU_CONSISTENCY_CASES = _filter_by_tag(ALL_CASES, "menu_consistency")
MENU_ACCESS_CONTROL_CASES = _filter_by_tag(ALL_CASES, "menu_access_control")


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
        path=case.get("path", "/cms/menu"),
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
    allure.dynamic.title(f"菜单管理 - {case['id']}")
    allure.dynamic.feature("菜单管理")
    allure.dynamic.story(case.get("tag", "菜单用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


# ===========================================================================
# 菜单查询 (TC-MENU-001 ~ TC-MENU-002)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_QUERY_CASES, ids=[c["id"] for c in MENU_QUERY_CASES])
def test_menu_query(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 参数校验 (TC-MENU-003)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_QUERY_VALIDATION_CASES, ids=[c["id"] for c in MENU_QUERY_VALIDATION_CASES])
def test_menu_query_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if expected.get("error"):
        _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 覆盖菜单 (TC-MENU-004)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_OVERRIDE_CASES, ids=[c["id"] for c in MENU_OVERRIDE_CASES])
def test_menu_override(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 覆盖异常校验 (TC-MENU-005)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_OVERRIDE_VALIDATION_CASES, ids=[c["id"] for c in MENU_OVERRIDE_VALIDATION_CASES])
def test_menu_override_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)


# ===========================================================================
# 覆盖后一致性 (TC-MENU-006)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_CONSISTENCY_CASES, ids=[c["id"] for c in MENU_CONSISTENCY_CASES])
def test_menu_consistency(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 未登录 (TC-MENU-007)
# ===========================================================================

@pytest.mark.menu
@pytest.mark.parametrize("case", MENU_ACCESS_CONTROL_CASES, ids=[c["id"] for c in MENU_ACCESS_CONTROL_CASES])
def test_menu_access_control(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)
