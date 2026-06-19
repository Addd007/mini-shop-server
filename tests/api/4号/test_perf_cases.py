"""
性能抽测 — 4号专项

测试依据：test_cases 4号 / 性能模块
数据来源：tests/cases/4号/perf_cases.yaml

测试分组：
  - perf              : 单接口响应时间抽测
  - perf_concurrent   : 并发性能测试

运行方式：
  pytest tests/api/4号/test_perf_cases.py -v
  pytest tests/api/4号/test_perf_cases.py -k TC-PERF-001
  pytest -m perf -v
"""

from __future__ import annotations

import concurrent.futures
import statistics
import time
from pathlib import Path
from typing import Any, List

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

CASE_FILE = "perf_cases.yaml"


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/perf_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
PERF_SINGLE_CASES = _filter_by_tag(ALL_CASES, "perf")
PERF_CONCURRENT_CASES = _filter_by_tag(ALL_CASES, "perf_concurrent")


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict) -> tuple:
    start = time.perf_counter()
    resp = client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/"),
        json=case.get("json"),
        params=case.get("params"),
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


def _concurrent_request(base_url: str, timeout: int, method: str, path: str, json_body=None, params=None) -> tuple:
    """单次并发请求 — 每个线程创建独立的 ApiClient 实例，避免 Session 共享"""
    client = ApiClient(base_url=base_url, timeout=timeout)
    start = time.perf_counter()
    try:
        resp = client.request(method=method, path=path, json=json_body, params=params)
        elapsed = (time.perf_counter() - start) * 1000
        return resp.status_code, elapsed, None
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return 0, elapsed, str(e)


# ===========================================================================
# 测试函数：单接口响应时间 (TC-PERF-001 ~ TC-PERF-003)
# ===========================================================================

@pytest.mark.perf
@pytest.mark.parametrize("case", PERF_SINGLE_CASES, ids=[c["id"] for c in PERF_SINGLE_CASES])
def test_performance_single(base_url, timeout, auth_client: ApiClient, client: ApiClient, case: dict):
    allure.dynamic.title(f"性能抽测 - {case['id']}")
    allure.dynamic.feature("性能抽测")
    allure.dynamic.story("单接口响应时间")

    if case.get("no_auth"):
        client_used = client
    else:
        client_used = auth_client

    resp, elapsed = _execute_case(client_used, case)
    expected = case.get("expected", {})
    max_ms = case.get("max_response_ms", 5000)
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if case.get("check_response_time"):
        with allure.step(f"校验响应时间 <= {max_ms}ms"):
            allure.attach(
                f"响应时间: {elapsed:.2f}ms (上限: {max_ms}ms)",
                name="响应时间",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert elapsed <= max_ms, (
                f"[{case['id']}] 响应时间 {elapsed:.2f}ms 超过上限 {max_ms}ms"
            )


# ===========================================================================
# 测试函数：并发登录 (TC-PERF-004)
# ===========================================================================

@pytest.mark.perf
def test_concurrent_login(base_url, timeout):
    """10 并发登录测试"""
    allure.dynamic.title("并发登录测试 - TC-PERF-004")
    allure.dynamic.feature("性能抽测")
    allure.dynamic.story("并发性能")

    results: List[tuple] = []
    with allure.step("10 并发登录"):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(
                    _concurrent_request, base_url, timeout,
                    "POST", "/v1/token",
                    {"account": "super", "secret": "123456", "type": 100},
                )
                for _ in range(10)
            ]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

    success_count = sum(1 for r in results if r[0] == 200)
    success_rate = success_count / len(results) if results else 0
    avg_time = statistics.mean([r[1] for r in results]) if results else 0

    allure.attach(
        f"成功率: {success_rate:.0%}, 平均耗时: {avg_time:.2f}ms, "
        f"各请求耗时: {[f'{r[1]:.0f}ms' for r in results]}",
        name="并发登录结果",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("校验成功率 >= 90%"):
        assert success_rate >= 0.9, f"并发登录成功率过低: {success_rate:.0%}"

    with allure.step("校验平均耗时 <= 2000ms"):
        assert avg_time <= 2000, f"并发登录平均耗时过高: {avg_time:.2f}ms"


# ===========================================================================
# 测试函数：并发查询 (TC-PERF-005)
# ===========================================================================

@pytest.mark.perf
def test_concurrent_query(base_url, timeout, auth_client: ApiClient):
    """20 并发查询测试"""
    allure.dynamic.title("并发查询测试 - TC-PERF-005")
    allure.dynamic.feature("性能抽测")
    allure.dynamic.story("并发性能")

    # 用 auth_client 获取 token，每个线程用独立 client 发起请求
    token = auth_client.token

    results: List[tuple] = []
    with allure.step("20 并发查询文件类型"):
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [
                executor.submit(
                    _concurrent_request, base_url, timeout,
                    "GET", "/cms/file/types",
                )
                for _ in range(20)
            ]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result())

    success_count = sum(1 for r in results if r[0] == 200)
    success_rate = success_count / len(results) if results else 0
    avg_time = statistics.mean([r[1] for r in results]) if results else 0

    allure.attach(
        f"成功率: {success_rate:.0%}, 平均耗时: {avg_time:.2f}ms, "
        f"各请求耗时: {[f'{r[1]:.0f}ms' for r in results]}",
        name="并发查询结果",
        attachment_type=allure.attachment_type.TEXT,
    )

    with allure.step("校验成功率 >= 95%"):
        assert success_rate >= 0.95, f"并发查询成功率过低: {success_rate:.0%}"

    with allure.step("校验平均耗时 <= 1000ms"):
        assert avg_time <= 1000, f"并发查询平均耗时过高: {avg_time:.2f}ms"
