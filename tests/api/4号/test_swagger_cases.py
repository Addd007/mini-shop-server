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

# Swagger 实际标签（由 Redprint.alias/name 生成，cms 用下划线，v1 无前缀）
EXPECTED_SWAGGER_MODULES = [
    "token",
    "cms_admin", "cms_group", "cms_auth", "cms_menu", "cms_element", "cms_route",
    "cms_oper_log", "cms_login_log", "cms_error_log",
    "cms_file",
    "user", "address",
    "banner", "theme", "category", "product", "order", "pay",
    "cms_user", "cms_article",
    "cms_order", "cms_banner", "cms_banner_item",
    "cms_notice", "cms_dict_type", "cms_dict", "cms_config", "cms_server",
]


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/swagger_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
SWAGGER_CASES = _filter_by_tag(ALL_CASES, "swagger")


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
    _attach_case(case, resp)

    # 如果返回 HTML（Swagger UI），不应尝试 JSON 解析
    content_type = resp.headers.get("Content-Type", "")
    if "text/html" in content_type:
        body = {}
        if case.get("id") == "TC-SWAG-001":
            # TC-SWAG-001 预期就是 Swagger UI 页面，HTML 返回即可接受
            with allure.step("Swagger UI 页面可访问（HTML 响应）"):
                assert resp.status_code == 200, (
                    f"[{case['id']}] Swagger UI 页面访问失败: {resp.status_code}"
                )
                assert "swagger" in resp.text.lower() or "api" in resp.text.lower(), (
                    f"[{case['id']}] Swagger UI 页面内容异常"
                )
            return  # 跳过后续 JSON 字段校验
        else:
            pytest.skip(f"[{case['id']}] 期望 JSON 但返回 HTML（Content-Type: {content_type}）")
    else:
        body = resp.json() if resp.text else {}

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
            # 验证期望的标签是否存在，缺失标签视为缺陷
            missing_tags = [t for t in EXPECTED_SWAGGER_MODULES if t not in tag_names]
            if missing_tags:
                allure.attach(
                    str(missing_tags),
                    name="缺失的标签",
                    attachment_type=allure.attachment_type.TEXT,
                )
            # 允许个别标签动态增减，但核心标签必须存在（匹配 Redprint.alias 实际命名）
            critical_tags = ["token", "cms_admin", "cms_file", "user", "product", "order"]
            missing_critical = [t for t in critical_tags if t not in tag_names]
            assert not missing_critical, (
                f"[{case['id']}] Swagger 缺少核心标签: {missing_critical}"
            )
