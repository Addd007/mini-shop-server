"""
权限组管理自动化测试

测试依据：test_cases/2号/group.md
数据来源：tests/cases/2号/group_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化用户测试数据

测试分组（按 YAML 中的 tag 字段划分）：
  - group_query            : 查询全部/单个权限组（TC-GROUP-001 ~ 003）
  - group_create           : 新建权限组（TC-GROUP-004）
  - group_create_validation: 新建异常校验（TC-GROUP-005）
  - group_update           : 更新权限组（TC-GROUP-006）
  - group_delete           : 删除权限组（TC-GROUP-007）
  - group_migrate          : 用户迁移（TC-GROUP-008）
  - group_access_control   : 越权 + 未登录（TC-GROUP-009 ~ 010）

运行方式：
  pytest tests/api/2号/test_group_cases.py -v
  pytest tests/api/2号/test_group_cases.py -k TC-GROUP-001
  pytest -m group -v
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


CASE_FILE = "cases/2号/group_cases.yaml"


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
GROUP_QUERY_CASES = _filter_by_tag(ALL_CASES, "group_query")
GROUP_CREATE_CASES = _filter_by_tag(ALL_CASES, "group_create")
GROUP_CREATE_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "group_create_validation")
GROUP_UPDATE_CASES = _filter_by_tag(ALL_CASES, "group_update")
GROUP_DELETE_CASES = _filter_by_tag(ALL_CASES, "group_delete")
GROUP_MIGRATE_CASES = _filter_by_tag(ALL_CASES, "group_migrate")
GROUP_ACCESS_CONTROL_CASES = _filter_by_tag(ALL_CASES, "group_access_control")


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
        path=case.get("path", "/cms/group/all"),
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
    allure.dynamic.title(f"权限组管理 - {case['id']}")
    allure.dynamic.feature("权限组管理")
    allure.dynamic.story(case.get("tag", "权限组用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


# ===========================================================================
# 查询权限组 (TC-GROUP-001 ~ TC-GROUP-003)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_QUERY_CASES, ids=[c["id"] for c in GROUP_QUERY_CASES])
def test_group_query(client: ApiClient, tokens: Dict[str, str], case: dict):
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
# 新建权限组 (TC-GROUP-004)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_CREATE_CASES, ids=[c["id"] for c in GROUP_CREATE_CASES])
def test_group_create(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 新建异常校验 (TC-GROUP-005)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_CREATE_VALIDATION_CASES, ids=[c["id"] for c in GROUP_CREATE_VALIDATION_CASES])
def test_group_create_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    with allure.step("校验错误响应"):
        _assert_error_response(case, resp, body)


# ===========================================================================
# 更新权限组 (TC-GROUP-006)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_UPDATE_CASES, ids=[c["id"] for c in GROUP_UPDATE_CASES])
def test_group_update(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 删除权限组 (TC-GROUP-007)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_DELETE_CASES, ids=[c["id"] for c in GROUP_DELETE_CASES])
def test_group_delete(client: ApiClient, tokens: Dict[str, str], case: dict):
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
# 用户迁移 (TC-GROUP-008)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_MIGRATE_CASES, ids=[c["id"] for c in GROUP_MIGRATE_CASES])
def test_group_migrate(client: ApiClient, tokens: Dict[str, str], case: dict):
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
# 越权 + 未登录 (TC-GROUP-009 ~ TC-GROUP-010)
# ===========================================================================

@pytest.mark.group
@pytest.mark.parametrize("case", GROUP_ACCESS_CONTROL_CASES, ids=[c["id"] for c in GROUP_ACCESS_CONTROL_CASES])
def test_group_access_control(client: ApiClient, tokens: Dict[str, str], case: dict):
    _skip_if_marked(case)
    resp, body = _run_case(client, tokens, case)
    with allure.step("校验错误响应"):
        _assert_error_response(case, resp, body)
