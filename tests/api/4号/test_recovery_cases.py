"""
异常恢复测试 — 4号专项

测试依据：test_cases 4号 / 异常恢复模块
数据来源：tests/cases/4号/recovery_cases.yaml

测试分组：
  - recovery : 异常恢复测试（健康检查/404/无效JSON/超大请求体/稳定性/SQL注入/超长参数）

运行方式：
  pytest tests/api/4号/test_recovery_cases.py -v
  pytest tests/api/4号/test_recovery_cases.py -k TC-RECOV-001
  pytest -m recovery -v
"""

from __future__ import annotations

import statistics
import time
from pathlib import Path
from typing import Any

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

CASE_FILE = "recovery_cases.yaml"

LONG_STRING = "A" * 5000
LARGE_PAYLOAD = "X" * 10000


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/recovery_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
RECOVERY_CASES = _filter_by_tag(ALL_CASES, "recovery")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def auth_client(base_url, timeout) -> ApiClient:
    """已认证的管理员客户端"""
    client = ApiClient(base_url=base_url, timeout=timeout)
    resp = client.request("POST", "/v1/token", json={
        "account": "super",
        "secret": "123456",
        "type": 100,
    })
    data = resp.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        pytest.skip("无法获取 Token，跳过需要认证的测试")
    return ApiClient(base_url=base_url, timeout=timeout, token=token)


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict) -> Any:
    return client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/health"),
        json=case.get("json"),
        params=case.get("params"),
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：健康检查 (TC-RECOV-001)
# ===========================================================================

@pytest.mark.recovery
def test_health_check(client: ApiClient):
    """健康检查端点可用"""
    allure.dynamic.title("健康检查 - TC-RECOV-001")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("健康检查")

    resp = client.request("GET", "/health")
    _attach_case({"id": "TC-RECOV-001"}, resp)

    with allure.step("校验 HTTP 200"):
        assert resp.status_code == 200, f"健康检查失败: {resp.status_code}"

    body = resp.json()
    with allure.step("校验返回 status=ok"):
        assert body.get("status") == "ok", f"健康检查状态异常: {body}"


# ===========================================================================
# 测试函数：404 处理 (TC-RECOV-002)
# ===========================================================================

@pytest.mark.recovery
def test_404_for_unknown_route(client: ApiClient):
    """请求不存在的路由返回 404"""
    allure.dynamic.title("404 处理 - TC-RECOV-002")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("错误处理")

    resp = client.request("GET", "/api/nonexistent_endpoint_xyz")
    _attach_case({"id": "TC-RECOV-002"}, resp)

    with allure.step("校验 HTTP 404"):
        assert resp.status_code == 404, (
            f"不存在的路由应返回 404, 实际: {resp.status_code}"
        )


# ===========================================================================
# 测试函数：无效 JSON 处理 (TC-RECOV-003)
# ===========================================================================

@pytest.mark.recovery
def test_invalid_json_handling(client: ApiClient):
    """无效 JSON 被正确处理"""
    allure.dynamic.title("无效JSON处理 - TC-RECOV-003")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("错误处理")

    resp = client.request(
        "POST", "/v1/token",
        data="{invalid json!!!}",
        headers={"Content-Type": "application/json"},
    )
    _attach_case({"id": "TC-RECOV-003"}, resp)

    with allure.step("校验返回 4xx 错误"):
        assert resp.status_code in (400, 415, 422), (
            f"无效 JSON 应返回 4xx, 实际: {resp.status_code}"
        )


# ===========================================================================
# 测试函数：超大请求体 (TC-RECOV-004)
# ===========================================================================

@pytest.mark.recovery
def test_large_request_body(auth_client: ApiClient):
    """超大请求体处理"""
    allure.dynamic.title("超大请求体处理 - TC-RECOV-004")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("错误处理")

    resp = auth_client.request("POST", "/v1/token", json={
        "account": "super",
        "secret": "123456",
        "type": 100,
        "junk_field": LARGE_PAYLOAD,
    })
    _attach_case({"id": "TC-RECOV-004"}, resp)

    assert resp.status_code in (200, 400, 413, 422), (
        f"超大请求体处理异常: {resp.status_code}"
    )


# ===========================================================================
# 测试函数：连续请求稳定性 (TC-RECOV-005)
# ===========================================================================

@pytest.mark.recovery
def test_continuous_requests_stability(auth_client: ApiClient):
    """连续 50 次请求验证服务稳定性"""
    allure.dynamic.title("连续请求稳定性 - TC-RECOV-005")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("稳定性")

    success_count = 0
    fail_count = 0
    response_times = []

    with allure.step("执行 50 次连续请求"):
        for i in range(50):
            start = time.perf_counter()
            try:
                resp = auth_client.request("GET", "/cms/file/types")
                elapsed = (time.perf_counter() - start) * 1000
                response_times.append(elapsed)
                if resp.status_code == 200:
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                fail_count += 1
                response_times.append(0)

    allure.attach(
        f"成功: {success_count}, 失败: {fail_count}, "
        f"平均耗时: {statistics.mean(response_times):.2f}ms, "
        f"最小: {min(response_times):.2f}ms, 最大: {max(response_times):.2f}ms",
        name="稳定性测试结果",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("校验成功率 >= 98%"):
        assert success_count >= 49, (
            f"连续请求成功率过低: {success_count}/50"
        )


# ===========================================================================
# 测试函数：SQL 注入防护 (TC-RECOV-006)
# ===========================================================================

@pytest.mark.recovery
def test_sql_injection_attempt(auth_client: ApiClient):
    """SQL 注入尝试被安全处理"""
    allure.dynamic.title("SQL注入防护 - TC-RECOV-006")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("安全")

    resp = auth_client.request("GET", "/cms/file/name/'; DROP TABLE file; --")
    _attach_case({"id": "TC-RECOV-006"}, resp)

    assert resp.status_code in (200, 404), (
        f"SQL 注入尝试不应导致 500: {resp.status_code}"
    )


# ===========================================================================
# 测试函数：超长参数处理 (TC-RECOV-007)
# ===========================================================================

@pytest.mark.recovery
def test_long_parameter_handling(auth_client: ApiClient):
    """超长参数处理"""
    allure.dynamic.title("超长参数处理 - TC-RECOV-007")
    allure.dynamic.feature("异常恢复")
    allure.dynamic.story("边界条件")

    resp = auth_client.request("GET", f"/cms/file/name/{LONG_STRING}")
    _attach_case({"id": "TC-RECOV-007"}, resp)

    assert resp.status_code in (200, 400, 404, 414), (
        f"超长参数处理异常: {resp.status_code}"
    )
