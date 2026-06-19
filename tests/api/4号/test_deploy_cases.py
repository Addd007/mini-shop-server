"""
部署配置验证 — 4号专项

测试依据：test_cases 4号 / 部署配置模块
数据来源：tests/cases/4号/deploy_cases.yaml

测试分组：
  - deploy : 部署配置验证（根路径/CORS/Content-Type/Flask-Admin/OPTIONS/默认路由）

运行方式：
  pytest tests/api/4号/test_deploy_cases.py -v
  pytest tests/api/4号/test_deploy_cases.py -k TC-DEPLOY-001
  pytest -m deploy -v
"""

from __future__ import annotations

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

CASE_FILE = "deploy_cases.yaml"


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/deploy_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
DEPLOY_CASES = _filter_by_tag(ALL_CASES, "deploy")


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict) -> tuple:
    """执行用例并返回 (resp, elapsed_ms)"""
    start = time.perf_counter()
    kwargs: dict = {}
    if "allow_redirects" in case:
        kwargs["allow_redirects"] = case["allow_redirects"]
    # CORS 预检请求需要发送 Origin 和 Access-Control-Request-Method 头
    if case.get("check_cors_preflight"):
        kwargs["headers"] = {
            "Origin": client.base_url,
            "Access-Control-Request-Method": "POST",
        }
    resp = client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/"),
        json=case.get("json"),
        params=case.get("params"),
        **kwargs,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：部署配置验证 (TC-DEPLOY-001 ~ TC-DEPLOY-006)
# ===========================================================================

@pytest.mark.deploy
@pytest.mark.parametrize("case", DEPLOY_CASES, ids=[c["id"] for c in DEPLOY_CASES])
def test_deploy(base_url, auth_client: ApiClient, client: ApiClient, case: dict):
    allure.dynamic.title(f"部署配置 - {case['id']}")
    allure.dynamic.feature("部署配置验证")
    allure.dynamic.story("部署配置")

    if case.get("no_auth"):
        client_used = client
    else:
        client_used = auth_client

    resp, elapsed = _execute_case(client_used, case)
    expected = case.get("expected", {})
    _attach_case(case, resp)

    # 附加性能数据
    allure.attach(
        f"{elapsed:.1f} ms",
        name="响应耗时",
        attachment_type=allure.attachment_type.TEXT,
    )

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    # 检查 CORS 头
    if case.get("check_cors"):
        with allure.step("校验 CORS 跨域头"):
            cors_header = resp.headers.get("Access-Control-Allow-Origin", "")
            assert cors_header in ("*", base_url), (
                f"[{case['id']}] CORS 头不正确: {cors_header}"
            )

    # 检查 Content-Type
    if case.get("check_content_type_json"):
        with allure.step("校验 JSON Content-Type"):
            content_type = resp.headers.get("Content-Type", "")
            assert "application/json" in content_type, (
                f"[{case['id']}] Content-Type 不是 JSON: {content_type}"
            )

    # 检查 CORS 预检
    if case.get("check_cors_preflight"):
        with allure.step("校验 CORS 预检响应头"):
            cors_origin = resp.headers.get("Access-Control-Allow-Origin", "")
            cors_methods = resp.headers.get("Access-Control-Allow-Methods", "")
            allure.attach(
                f"Access-Control-Allow-Origin: {cors_origin}\n"
                f"Access-Control-Allow-Methods: {cors_methods}",
                name="CORS 预检头",
                attachment_type=allure.attachment_type.TEXT,
            )
            # 补充断言：预检响应应包含有效的 CORS 头
            assert cors_origin, (
                f"[{case['id']}] 缺少 Access-Control-Allow-Origin 头"
            )
            assert cors_methods, (
                f"[{case['id']}] 缺少 Access-Control-Allow-Methods 头"
            )
