"""
操作日志自动化测试

测试依据：test_cases/2号/oper_log.md（1号预写）
数据来源：tests/cases/2号/oper_log_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化用户测试数据

测试分组（按 YAML 中的 tag 字段划分）：
  - oper_search              : 操作日志搜索（TC-OPER-001 ~ 006）
  - oper_search_validation   : 搜索参数校验（TC-OPER-005, 009）
  - oper_user_list           : 用户列表日志（TC-OPER-010）
  - oper_user_list_validation: 用户列表参数校验（TC-OPER-011）
  - oper_detail              : 操作日志详情（TC-OPER-014 ~ 015）
  - oper_detail_validation   : 详情参数校验（TC-OPER-016）
  - oper_delete              : 删除日志（TC-OPER-019 ~ 020）
  - oper_delete_validation   : 删除参数校验（TC-OPER-021）
  - oper_clear               : 清空日志（TC-OPER-024）
  - oper_access_control      : 越权 + 未登录（TC-OPER-007~008, 012~013, 017~018, 022~023, 025~026）

⚠️ 注意：TC-OPER-024 会清空全部 oper_log 数据，建议最后执行

运行方式：
  pytest tests/api/2号/test_oper_log_cases.py -v
  pytest tests/api/2号/test_oper_log_cases.py -k TC-OPER-001
  pytest -m oper_log -v
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


CASE_FILE = "cases/2号/oper_log_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [c for c in cases if c.get("tag") == tag]


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


ALL_CASES = _load_cases()
OPER_SEARCH_CASES = _filter_by_tag(ALL_CASES, "oper_search")
OPER_SEARCH_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "oper_search_validation")
OPER_USER_LIST_CASES = _filter_by_tag(ALL_CASES, "oper_user_list")
OPER_USER_LIST_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "oper_user_list_validation")
OPER_DETAIL_CASES = _filter_by_tag(ALL_CASES, "oper_detail")
OPER_DETAIL_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "oper_detail_validation")
OPER_DELETE_CASES = _filter_by_tag(ALL_CASES, "oper_delete")
OPER_DELETE_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "oper_delete_validation")
OPER_CLEAR_CASES = _filter_by_tag(ALL_CASES, "oper_clear")
OPER_ACCESS_CONTROL_CASES = _filter_by_tag(ALL_CASES, "oper_access_control")


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
        path=case.get("path", "/cms/log/oper/list/search"),
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
    allure.dynamic.title(f"操作日志 - {case['id']}")
    allure.dynamic.feature("操作日志")
    allure.dynamic.story(case.get("tag", "操作日志用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


# ===========================================================================
# 操作日志搜索 (TC-OPER-001 ~ TC-OPER-006)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_SEARCH_CASES, ids=[c["id"] for c in OPER_SEARCH_CASES])
def test_oper_search(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 搜索参数校验 (TC-OPER-005, TC-OPER-009)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_SEARCH_VALIDATION_CASES, ids=[c["id"] for c in OPER_SEARCH_VALIDATION_CASES])
def test_oper_search_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)


# ===========================================================================
# 用户列表日志 (TC-OPER-010)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_USER_LIST_CASES, ids=[c["id"] for c in OPER_USER_LIST_CASES])
def test_oper_user_list(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 用户列表参数校验 (TC-OPER-011)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_USER_LIST_VALIDATION_CASES, ids=[c["id"] for c in OPER_USER_LIST_VALIDATION_CASES])
def test_oper_user_list_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)


# ===========================================================================
# 操作日志详情 (TC-OPER-014 ~ TC-OPER-015)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_DETAIL_CASES, ids=[c["id"] for c in OPER_DETAIL_CASES])
def test_oper_detail(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if expected.get("error"):
        _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 详情参数校验 (TC-OPER-016)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_DETAIL_VALIDATION_CASES, ids=[c["id"] for c in OPER_DETAIL_VALIDATION_CASES])
def test_oper_detail_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)


# ===========================================================================
# 删除日志 (TC-OPER-019 ~ TC-OPER-020)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_DELETE_CASES, ids=[c["id"] for c in OPER_DELETE_CASES])
def test_oper_delete(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if expected.get("error"):
        _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 删除参数校验 (TC-OPER-021)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_DELETE_VALIDATION_CASES, ids=[c["id"] for c in OPER_DELETE_VALIDATION_CASES])
def test_oper_delete_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)


# ===========================================================================
# 清空日志 (TC-OPER-024) ⚠️ 会清空全部数据
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_CLEAR_CASES, ids=[c["id"] for c in OPER_CLEAR_CASES])
def test_oper_clear(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})
    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 越权 + 未登录 (TC-OPER-007~008, 012~013, 017~018, 022~023, 025~026)
# ===========================================================================

@pytest.mark.oper_log
@pytest.mark.parametrize("case", OPER_ACCESS_CONTROL_CASES, ids=[c["id"] for c in OPER_ACCESS_CONTROL_CASES])
def test_oper_access_control(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    _assert_error_response(case, resp, body)
