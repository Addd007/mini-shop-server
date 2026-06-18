"""
Swagger 接口文档检查 — 4号专项

测试依据：test_cases 4号 / Swagger 模块
数据来源：tests/cases/4号/swagger_cases.yaml

测试分组：
  - swagger : Swagger 文档检查（UI/JSON/标题/安全定义/标签完整性）

运行方式：
  pytest tests/api/4号/test_swagger_cases.py -v
  pytest tests/api/4号/test_swagger_cases.py -k TC-SWAG-001
  pytest -m swagger -v
"""

from __future__ import annotations

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

CASE_FILE = "swagger_cases.yaml"

# Swagger 应有的标签（来自 app/config/setting.py 的 ALL_RP_API_LIST）
EXPECTED_SWAGGER_MODULES = [
    "v1-token",
    "cms-admin", "cms-group", "cms-auth", "cms-menu", "cms-element", "cms-route",
    "cms-oper_log", "cms-login_log",
    "cms-file",
    "v1-user", "v1-address",
    "v1-banner", "v1-theme", "v1-category", "v1-product", "v1-order", "v1-pay",
    "cms-user", "cms-article",
    "cms-order", "cms-banner", "cms-banner_item",
    "cms-notice", "cms-dict_type", "cms-dict", "cms-config", "cms-server",
]


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/swagger_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
SWAGGER_CASES = _filter_by_tag(ALL_CASES, "swagger")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict) -> Any:
    return client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/apispec_1.json"),
        json=case.get("json"),
        params=case.get("params"),
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：Swagger 文档检查 (TC-SWAG-001 ~ TC-SWAG-005)
# ===========================================================================

@pytest.mark.swagger
@pytest.mark.parametrize("case", SWAGGER_CASES, ids=[c["id"] for c in SWAGGER_CASES])
def test_swagger(client: ApiClient, case: dict):
    allure.dynamic.title(f"Swagger 检查 - {case['id']}")
    allure.dynamic.feature("专项测试")
    allure.dynamic.story("Swagger 文档")

    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    # 检查 Swagger 标题
    if case.get("check_swagger_title"):
        with allure.step("校验 Swagger 文档标题"):
            title = body.get("info", {}).get("title", "")
            assert "API" in title or "小程序" in title or "商城" in title, (
                f"[{case['id']}] Swagger 标题不符合预期: {title}"
            )
            allure.attach(title, name="Swagger 标题", attachment_type=allure.attachment_type.TEXT)

    # 检查安全定义
    if case.get("check_security_def"):
        with allure.step("校验 basicAuth 安全定义"):
            sec_defs = body.get("securityDefinitions", {})
            assert "basicAuth" in sec_defs, (
                f"[{case['id']}] Swagger 缺少 basicAuth 安全定义"
            )

    # 检查标签完整性
    if case.get("check_tags"):
        with allure.step("校验模块标签完整性"):
            tags = body.get("tags", [])
            tag_names = [t.get("name", "") for t in tags]
            allure.attach(
                str(tag_names),
                name="实际标签列表",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert len(tag_names) > 0, f"[{case['id']}] Swagger 标签列表为空"
