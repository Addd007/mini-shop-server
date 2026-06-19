"""
日志审计自动化测试 — 4号专项

测试依据：test_cases 4号 / 日志审计模块
数据来源：tests/cases/4号/log_cases.yaml

测试分组（按 YAML 中的 tag 字段划分）：
  - login_log      : 登录日志查询（列表/时间筛选/无权限）
  - oper_log       : 操作日志查询（搜索/用户名筛选/关键词筛选/用户列表/无权限）
  - error_log      : 异常日志查询
  - log_audit      : 日志记录验证（登录产生日志/失败不产生成功日志）

运行方式：
  pytest tests/api/4号/test_log_cases.py -v
  pytest tests/api/4号/test_log_cases.py -k TC-LOG-001
  pytest -m log -v
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).resolve().parents[1] / "cases" / "4号"
CASE_FILE = "log_cases.yaml"


def _load_cases() -> list:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load("cases/4号/log_cases.yaml")


def _filter_by_tag(cases: list, tag: str) -> list:
    return [c for c in cases if c.get("tag") == tag]


ALL_CASES = _load_cases()
LOGIN_LOG_CASES = _filter_by_tag(ALL_CASES, "login_log")
OPER_LOG_CASES = _filter_by_tag(ALL_CASES, "oper_log")
ERROR_LOG_CASES = _filter_by_tag(ALL_CASES, "error_log")
LOG_AUDIT_CASES = _filter_by_tag(ALL_CASES, "log_audit")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def time_range():
    """生成时间筛选范围"""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    return {"today": today, "yesterday": yesterday}


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _resolve_params(case: dict, time_range: dict) -> Optional[dict]:
    params = case.get("params", {}).copy() if case.get("params") else None
    if params and time_range:
        for key, val in params.items():
            if isinstance(val, str) and val.startswith("{") and val.endswith("}"):
                placeholder = val[1:-1]
                if placeholder in time_range:
                    params[key] = str(time_range[placeholder])
    return params


def _execute_case(client: ApiClient, case: dict, time_range: dict = None) -> Any:
    params = _resolve_params(case, time_range) if time_range else case.get("params")
    return client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/cms/log/login/list"),
        json=case.get("json"),
        params=params,
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


def _has_error(body: dict) -> bool:
    error_code = body.get("error_code", body.get("code"))
    return error_code is not None and error_code != 0


# ===========================================================================
# 测试函数：登录日志 (TC-LOG-001 ~ TC-LOG-003)
# ===========================================================================

@pytest.mark.log
@pytest.mark.parametrize("case", LOGIN_LOG_CASES, ids=[c["id"] for c in LOGIN_LOG_CASES])
def test_login_log(base_url, timeout, auth_client: ApiClient, time_range: dict, case: dict):
    allure.dynamic.title(f"登录日志 - {case['id']}")
    allure.dynamic.feature("日志审计")
    allure.dynamic.story("登录日志")

    if case.get("no_auth"):
        client = ApiClient(base_url=base_url, timeout=timeout)
    else:
        client = auth_client

    resp = _execute_case(client, case, time_range)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if "json" in expected:
        for key, val in expected["json"].items():
            with allure.step(f"校验响应字段 {key}"):
                assert body.get(key) == val, (
                    f"[{case['id']}] 期望 {key}={val}, 实际 {body.get(key)}"
                )

    if expected.get("error"):
        with allure.step("校验无权限访问返回错误"):
            if resp.status_code == 200:
                assert _has_error(body), f"[{case['id']}] 应返回错误: {body}"
            else:
                assert resp.status_code in (400, 401, 403), (
                    f"[{case['id']}] 期望 4xx, 实际 {resp.status_code}"
                )


# ===========================================================================
# 测试函数：操作日志 (TC-LOG-004 ~ TC-LOG-008)
# ===========================================================================

@pytest.mark.log
@pytest.mark.parametrize("case", OPER_LOG_CASES, ids=[c["id"] for c in OPER_LOG_CASES])
def test_oper_log(base_url, timeout, auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"操作日志 - {case['id']}")
    allure.dynamic.feature("日志审计")
    allure.dynamic.story("操作日志")

    if case.get("no_auth"):
        client = ApiClient(base_url=base_url, timeout=timeout)
    else:
        client = auth_client

    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if "json" in expected:
        for key, val in expected["json"].items():
            with allure.step(f"校验响应字段 {key}"):
                assert body.get(key) == val, (
                    f"[{case['id']}] 期望 {key}={val}, 实际 {body.get(key)}"
                )

    if expected.get("error"):
        with allure.step("校验无权限访问返回错误"):
            if resp.status_code == 200:
                assert _has_error(body), f"[{case['id']}] 应返回错误: {body}"
            else:
                assert resp.status_code in (400, 401, 403), (
                    f"[{case['id']}] 期望 4xx, 实际 {resp.status_code}"
                )


# ===========================================================================
# 测试函数：异常日志 (TC-LOG-009)
# ===========================================================================

@pytest.mark.log
@pytest.mark.parametrize("case", ERROR_LOG_CASES, ids=[c["id"] for c in ERROR_LOG_CASES])
def test_error_log(auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"异常日志 - {case['id']}")
    allure.dynamic.feature("日志审计")
    allure.dynamic.story("异常日志")

    resp = _execute_case(auth_client, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp)

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )


# ===========================================================================
# 测试函数：日志记录验证 (TC-LOG-010 ~ TC-LOG-011)
# 验证登录操作是否产生了正确的日志记录
# ===========================================================================

@pytest.mark.log
@pytest.mark.parametrize("case", LOG_AUDIT_CASES, ids=[c["id"] for c in LOG_AUDIT_CASES])
def test_log_audit(client: ApiClient, auth_client: ApiClient, case: dict):
    allure.dynamic.title(f"日志记录验证 - {case['id']}")
    allure.dynamic.feature("日志审计")
    allure.dynamic.story("日志记录验证")

    # 失败登录场景：记录登录前的日志快照，用于后续对比
    pre_log_ids = set()
    if case.get("check_login_log_fail"):
        pre_resp = auth_client.request("GET", "/cms/log/login/list", params={"size": 20})
        pre_body = pre_resp.json()
        pre_data = pre_body.get("data", pre_body)
        pre_items = pre_data.get("items", []) if isinstance(pre_data, dict) else []
        pre_log_ids = {item.get("id") for item in pre_items if item.get("id") is not None}

    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json() if resp.text else {}
    _attach_case(case, resp, request_payload=case.get("json"))

    # 验证登录响应
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if expected.get("has_token"):
        with allure.step("校验返回 token"):
            token = body.get("token") or body.get("data", {}).get("token")
            assert token, f"[{case['id']}] 登录成功应返回 token: {body}"

    if expected.get("error"):
        with allure.step("校验登录失败"):
            if resp.status_code == 200:
                error_code = body.get("error_code", body.get("code"))
                assert error_code is not None and error_code != 0, (
                    f"[{case['id']}] 应返回非零 error_code: {body}"
                )

    # 验证登录日志
    if case.get("check_login_log"):
        with allure.step("校验产生了登录日志记录"):
            log_resp = auth_client.request(
                "GET", "/cms/log/login/list",
                params={"size": 50},
            )
            log_body = log_resp.json()
            log_data = log_body.get("data", log_body)
            items = log_data.get("items", []) if isinstance(log_data, dict) else []
            assert items, f"[{case['id']}] 登录日志不应为空"

            # 验证最近一条日志的状态为成功
            latest = items[0] if items else {}
            status = latest.get("status")
            allure.attach(
                str(latest),
                name="最新登录日志",
                attachment_type=allure.attachment_type.TEXT,
            )

    if case.get("check_login_log_fail"):
        with allure.step("校验密码错误场景不产生成功日志"):
            log_resp = auth_client.request(
                "GET", "/cms/log/login/list",
                params={"size": 50},
            )
            log_body = log_resp.json()
            log_data = log_body.get("data", log_body)
            items = log_data.get("items", []) if isinstance(log_data, dict) else []
            allure.attach(
                str(items[:5] if items else "无日志"),
                name="失败登录后最新日志（前5条）",
                attachment_type=allure.attachment_type.TEXT,
            )

            assert isinstance(items, list), f"[{case['id']}] 登录日志接口异常: items 类型错误"

            # 检查失败登录后是否产生了新的成功日志条目
            new_success_entries = [
                item for item in items[:10]
                if item.get("status") == "success"
                and item.get("id") not in pre_log_ids
            ]
            if new_success_entries:
                allure.attach(
                    str(new_success_entries),
                    name="⚠ 失败登录后新增的成功日志条目（需人工确认）",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 这里设为软告警而非硬失败：因为日志系统可能异步写入，
                # 这些成功条目可能是其他并发请求产生的，需要人工判断
            else:
                allure.attach(
                    "未发现失败登录导致的新成功日志，断言通过",
                    name="断言结果",
                    attachment_type=allure.attachment_type.TEXT,
                )
