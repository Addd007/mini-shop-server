"""
登录日志接口自动化测试

测试依据：test_cases/1号/login_log.md
数据来源：tests/cases/1号/login_log.yaml（YAML 数据驱动，新增用例只需编辑 YAML）
前置条件：服务已启动，且已执行 fake.py 初始化登录日志数据

测试分组（按 YAML 中的 tag 字段划分）：
  - login_log_list   : 登录日志列表（TC-LOGIN-001 ~ 009）
  - login_log_detail : 登录日志详情（TC-LOGIN-010 ~ 014）
  - login_log_delete : 删除登录日志（TC-LOGIN-015 ~ 019）
  - login_log_clear  : 清空登录日志（TC-LOGIN-020 ~ 022）

运行方式：
  pytest tests/api/1号/test_login_log_cases.py -v            # 全量运行
  pytest tests/api/1号/test_login_log_cases.py -k TC-LOGIN-001  # 按用例 ID 筛选
  pytest -m login_log -v                                      # 按 marker 筛选
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import subprocess
import sys

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


CASE_FILE = "cases/1号/login_log.yaml"


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [c for c in cases if c.get("tag") == tag]


def _extract_token(resp_json: dict) -> str | None:
    return resp_json.get("token") or resp_json.get("data", {}).get("token")


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


@pytest.fixture(scope="module", autouse=True)
def initialize_test_data():
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[3] / "fake.py"), "--scope", "login_log"], check=True)
    yield
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[3] / "fake.py"), "--scope", "login_log"], check=True)


ALL_CASES = _load_cases()
LOGIN_LOG_LIST_CASES = _filter_by_tag(ALL_CASES, "login_log_list")
LOGIN_LOG_DETAIL_CASES = _filter_by_tag(ALL_CASES, "login_log_detail")
LOGIN_LOG_DELETE_CASES = _filter_by_tag(ALL_CASES, "login_log_delete")
LOGIN_LOG_CLEAR_CASES = _filter_by_tag(ALL_CASES, "login_log_clear")


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    accounts = [
        ("super", "super", "123456"),
        ("admin", "admin", "123456"),
        ("user", "user", "123456"),
    ]
    result: Dict[str, str] = {}
    for name, account, secret in accounts:
        resp = client.request(
            "POST",
            "/v1/token",
            json={"account": account, "secret": secret, "type": 100},
        )
        token = _extract_token(resp.json())
        if token:
            result[name] = token
    return result


def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    if auth == "none" or not auth:
        return ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    return ApiClient(base_url=client.base_url, timeout=client.timeout, token=tokens.get(auth))


def _execute_case(client: ApiClient, tokens: Dict[str, str], case: dict) -> Any:
    auth_client = _get_auth_client(client, tokens, case.get("auth", "none"))
    return auth_client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/cms/log/login/list"),
        json=case.get("json") if case.get("json") else None,
        params=case.get("params"),
        headers=case.get("headers"),
    )


def _assert_error_response(case: dict, resp, body: dict):
    if resp.status_code == 200:
        assert _has_error(body), f"[{case['id']}] 业务应返回非零 error_code: {body}"
    else:
        assert resp.status_code in (400, 401, 403, 404, 422, 500), (
            f"[{case['id']}] 期望 4xx/5xx, 实际 {resp.status_code}"
        )


def _run_case(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"登录日志接口 - {case['id']}")
    allure.dynamic.feature("登录日志管理")
    allure.dynamic.story(case.get("tag", "登录日志用例"))
    resp = _execute_case(client, tokens, case)
    body = resp.json()
    attach_request_response({"case": case}, resp)
    return resp, body


@pytest.mark.login_log
@pytest.mark.parametrize("case", LOGIN_LOG_LIST_CASES, ids=[c["id"] for c in LOGIN_LOG_LIST_CASES])
def test_login_log_list(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    else:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )


@pytest.mark.login_log
@pytest.mark.parametrize("case", LOGIN_LOG_DETAIL_CASES, ids=[c["id"] for c in LOGIN_LOG_DETAIL_CASES])
def test_login_log_detail(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    else:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )


@pytest.mark.login_log
@pytest.mark.parametrize("case", LOGIN_LOG_DELETE_CASES, ids=[c["id"] for c in LOGIN_LOG_DELETE_CASES])
def test_login_log_delete(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    else:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )


@pytest.mark.login_log
@pytest.mark.parametrize("case", LOGIN_LOG_CLEAR_CASES, ids=[c["id"] for c in LOGIN_LOG_CLEAR_CASES])
def test_login_log_clear(client: ApiClient, tokens: Dict[str, str], case: dict):
    resp, body = _run_case(client, tokens, case)
    expected = case.get("expected", {})

    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
    else:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
