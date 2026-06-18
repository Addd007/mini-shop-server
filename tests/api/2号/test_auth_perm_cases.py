"""
权限分配管理自动化测试

测试依据：test_cases/2号/auth_perm.md
数据来源：tests/cases/2号/auth_perm_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化用户测试数据

测试分组（按 YAML 中的 tag 字段划分）：
  - perm_query            : 权限查询（TC-PERM-001 ~ 002）
  - perm_query_validation : 参数校验（TC-PERM-003）
  - perm_append           : 新增权限（TC-PERM-004）
  - perm_append_validation: 新增异常校验（TC-PERM-005）
  - perm_remove           : 移除权限（TC-PERM-006）
  - perm_delete_all       : 删除全部权限（TC-PERM-007）
  - perm_access_control   : 越权 + 未登录（TC-PERM-008 ~ 009）

运行方式：
  pytest tests/api/2号/test_auth_perm_cases.py -v            # 全量运行
  pytest tests/api/2号/test_auth_perm_cases.py -k TC-PERM-001  # 按用例 ID 筛选
  pytest -m auth_perm -v                                       # 按 marker 筛选
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.auth_seed import get_test_tokens
from tests.common.case_loader import CaseLoader


# ---------------------------------------------------------------------------
# 常量：YAML 用例文件路径
# ---------------------------------------------------------------------------

CASE_FILE = "cases/2号/auth_perm_cases.yaml"


# ---------------------------------------------------------------------------
# 数据加载工具函数
# ---------------------------------------------------------------------------

def _load_cases() -> list[dict[str, Any]]:
    """从 YAML 文件加载全部测试用例"""
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    """按 tag 字段过滤用例"""
    return [c for c in cases if c.get("tag") == tag]


def _has_error(resp_json: dict) -> bool:
    """判断响应 JSON 是否包含业务错误（error_code 非零）"""
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


# ---------------------------------------------------------------------------
# 模块级加载用例数据（只读取一次 YAML，按 tag 拆分）
# ---------------------------------------------------------------------------

ALL_CASES = _load_cases()
PERM_QUERY_CASES = _filter_by_tag(ALL_CASES, "perm_query")
PERM_QUERY_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "perm_query_validation")
PERM_APPEND_CASES = _filter_by_tag(ALL_CASES, "perm_append")
PERM_APPEND_VALIDATION_CASES = _filter_by_tag(ALL_CASES, "perm_append_validation")
PERM_REMOVE_CASES = _filter_by_tag(ALL_CASES, "perm_remove")
PERM_DELETE_ALL_CASES = _filter_by_tag(ALL_CASES, "perm_delete_all")
PERM_ACCESS_CONTROL_CASES = _filter_by_tag(ALL_CASES, "perm_access_control")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    """模块级 HTTP 客户端"""
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    """预先登录多个测试账号，获取各自的 token。"""
    return get_test_tokens(client)


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    """
    根据用例的 auth 字段返回带对应 token 的客户端。

    auth 可选值：super / user / none
    - super: 超级管理员（admin_required 接口的正向测试）
    - user:  普通用户（越权测试）
    - none:  未登录（未认证测试）
    """
    if auth == "none" or not auth:
        return ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    token = tokens.get(auth)
    return ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)


def _execute_case(client: ApiClient, tokens: Dict[str, str], case: dict) -> Any:
    """根据 YAML 用例字典构造并发送 HTTP 请求"""
    auth = case.get("auth", "none")
    auth_client = _get_auth_client(client, tokens, auth)

    method = case.get("method", "GET")
    path = case.get("path", "/cms/auth/all")
    json_body = case.get("json") if case.get("json") else None
    headers = case.get("headers")
    params = case.get("params")

    return auth_client.request(
        method=method,
        path=path,
        json=json_body,
        headers=headers,
        params=params,
    )


def _assert_error_response(case: dict, resp, body: dict):
    """断言错误响应：HTTP 4xx 或 error_code 非零"""
    if resp.status_code == 200:
        assert _has_error(body), (
            f"[{case['id']}] 业务应返回非零 error_code: {body}"
        )
    else:
        assert resp.status_code in (400, 401, 403, 404, 422, 500), (
            f"[{case['id']}] 期望 4xx/5xx, 实际 {resp.status_code}"
        )


def _run_case(client: ApiClient, tokens: Dict[str, str], case: dict):
    """公共：执行用例并附加 Allure 报告"""
    allure.dynamic.title(f"权限管理 - {case['id']}")
    allure.dynamic.feature("权限分配管理")
    allure.dynamic.story(case.get("tag", "权限用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


# ===========================================================================
# 权限查询 (TC-PERM-001 ~ TC-PERM-002)
# 验证点：HTTP 200，返回权限列表
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_QUERY_CASES,
    ids=[c["id"] for c in PERM_QUERY_CASES],
)
def test_perm_query(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 参数校验 (TC-PERM-003)
# 验证点：group_id 为空应被拦截，不存在返回空列表
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_QUERY_VALIDATION_CASES,
    ids=[c["id"] for c in PERM_QUERY_VALIDATION_CASES],
)
def test_perm_query_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验参数错误响应"):
            _assert_error_response(case, resp, body)
    elif "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 新增权限 (TC-PERM-004)
# 验证点：为权限组追加权限成功
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_APPEND_CASES,
    ids=[c["id"] for c in PERM_APPEND_CASES],
)
def test_perm_append(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 新增异常校验 (TC-PERM-005)
# 验证点：group_id 为空 / auth_ids 为空应被拦截
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_APPEND_VALIDATION_CASES,
    ids=[c["id"] for c in PERM_APPEND_VALIDATION_CASES],
)
def test_perm_append_validation(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验参数错误响应"):
            _assert_error_response(case, resp, body)


# ===========================================================================
# 移除权限 (TC-PERM-006)
# 验证点：从权限组移除权限成功
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_REMOVE_CASES,
    ids=[c["id"] for c in PERM_REMOVE_CASES],
)
def test_perm_remove(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 删除全部权限 (TC-PERM-007)
# 验证点：删除某权限组的所有权限成功
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_DELETE_ALL_CASES,
    ids=[c["id"] for c in PERM_DELETE_ALL_CASES],
)
def test_perm_delete_all(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 越权 + 未登录 (TC-PERM-008 ~ TC-PERM-009)
# 验证点：普通用户被拒 / 未登录被拒
# ===========================================================================

@pytest.mark.auth_perm
@pytest.mark.parametrize(
    "case",
    PERM_ACCESS_CONTROL_CASES,
    ids=[c["id"] for c in PERM_ACCESS_CONTROL_CASES],
)
def test_perm_access_control(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验访问被拒绝"):
            _assert_error_response(case, resp, body)
