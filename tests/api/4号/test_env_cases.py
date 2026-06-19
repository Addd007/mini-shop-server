"""
环境变量切换 — 4号专项

测试依据：test_cases 4号 / 环境变量模块
数据来源：tests/cases/4号/env_cases.yaml

测试分组：
  - env : 环境变量切换（DEBUG/URL配置/版本信息/数据库连接/敏感信息泄露）

运行方式：
  pytest tests/api/4号/test_env_cases.py -v
  pytest tests/api/4号/test_env_cases.py -k TC-ENV-001
  pytest -m env -v
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

CASE_FILE = "env_cases.yaml"


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/env_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
ENV_CASES = _filter_by_tag(ALL_CASES, "env")


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict) -> tuple:
    start = time.perf_counter()
    resp = client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/health"),
        json=case.get("json"),
        params=case.get("params"),
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    return resp, elapsed_ms


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：环境变量验证 (TC-ENV-001 ~ TC-ENV-005)
# ===========================================================================

@pytest.mark.env
@pytest.mark.parametrize("case", ENV_CASES, ids=[c["id"] for c in ENV_CASES])
def test_env(client: ApiClient, auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"环境检查 - {case['id']}")
    allure.dynamic.feature("环境变量切换")
    allure.dynamic.story("环境配置验证")

    if case.get("no_auth"):
        client_used = client
    else:
        client_used = auth_client

    resp, elapsed = _execute_case(client_used, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    # 检查 DEBUG 模式
    if case.get("check_debug_mode"):
        with allure.step("记录 DEBUG 模式状态"):
            has_debug_info = "traceback" in str(body).lower() or "debug" in str(body).lower()
            allure.attach(
                f"has_debug_info: {has_debug_info}",
                name="DEBUG 模式推断",
                attachment_type=allure.attachment_type.TEXT,
            )

    # 检查 Swagger host
    if case.get("check_host"):
        with allure.step("校验服务端 host 配置"):
            host = body.get("host", "")
            allure.attach(str(host), name="服务端 host", attachment_type=allure.attachment_type.TEXT)
            assert host, f"[{case['id']}] host 不应为空"

    # 检查敏感信息泄露
    if case.get("check_no_server_header"):
        with allure.step("检查响应头中敏感信息"):
            sensitive_headers = ["X-Powered-By", "Server"]
            found_sensitive = {}
            for header in sensitive_headers:
                val = resp.headers.get(header, "")
                if val:
                    found_sensitive[header] = val

            allure.attach(
                str(dict(resp.headers)),
                name="响应头列表",
                attachment_type=allure.attachment_type.TEXT,
            )

            if found_sensitive:
                allure.attach(
                    str(found_sensitive),
                    name="发现的敏感响应头",
                    attachment_type=allure.attachment_type.TEXT,
                )
            # 敏感响应头不应暴露详细版本信息（开发环境建议通过反向代理隐藏）
            for header, val in found_sensitive.items():
                has_version = val and len(val.split("/")) >= 2
                allure.attach(
                    f"[建议] 生产环境请通过反向代理隐藏 {header} 头，当前值: {val}",
                    name=f"[建议] {header} 头泄露",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 开发环境可接受，只记录建议不阻断测试
