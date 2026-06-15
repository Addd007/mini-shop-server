"""
登录与鉴权自动化测试

测试依据：test_cases/1号/auth.md
数据来源：tests/cases/auth/auth_cases.yaml（YAML 数据驱动，新增用例只需编辑 YAML）
前置条件：服务已启动，且已执行 fake.py 初始化测试账号

测试分组（按 YAML 中的 tag 字段划分）：
  - login_success : 正常登录（用户名/邮箱/手机号），验证返回有效 Token
  - login_failure : 异常登录（密码错误/账号不存在/类型无效等），验证不返回 Token
  - validation    : 参数校验（空账号/空密码/缺失 type），验证接口拦截
  - token_verify  : Token 校验接口（空/伪造/有效 Token），验证鉴权逻辑

运行方式：
  pytest tests/api/1号/test_auth_cases.py -v           # 全量运行
  pytest tests/api/1号/test_auth_cases.py -k TC-AUTH-001  # 按用例 ID 筛选
  pytest -m auth -v                                # 按 marker 筛选
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


# ---------------------------------------------------------------------------
# 常量：YAML 用例文件路径（相对于 tests/ 目录）
# ---------------------------------------------------------------------------

CASES_DIR = Path(__file__).resolve().parents[1] / "cases" / "1号"
CASE_FILE = "auth_cases.yaml"


# ---------------------------------------------------------------------------
# 数据加载工具函数
# ---------------------------------------------------------------------------

def _load_cases() -> list[dict[str, Any]]:
    """
    从 YAML 文件加载全部测试用例。
    CaseLoader 以 tests/ 目录为基准，传入相对路径。
    """
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(f"cases/1号/{CASE_FILE}")


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    """
    按 tag 字段过滤用例。
    tag 对应 YAML 中每条用例的分组标识（login_success / login_failure / validation / token_verify）。
    """
    return [c for c in cases if c.get("tag") == tag]


def _extract_token(resp_json: dict) -> Optional[str]:
    """
    从响应 JSON 中提取 token。
    兼容两种响应结构：
      - 直接返回 {"token": "xxx"}
      - 嵌套返回 {"data": {"token": "xxx"}}
    """
    return resp_json.get("token") or resp_json.get("data", {}).get("token")


def _has_error(resp_json: dict) -> bool:
    """
    判断响应 JSON 是否包含业务错误。
    业务约定：error_code（或 code）为非零值表示出错。
    """
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


# ---------------------------------------------------------------------------
# 模块级加载用例数据（只读取一次 YAML，按 tag 拆分为四组）
# ---------------------------------------------------------------------------

ALL_CASES = _load_cases()
LOGIN_SUCCESS_CASES = _filter_by_tag(ALL_CASES, "login_success")   # TC-AUTH-001 ~ 010
LOGIN_FAILURE_CASES = _filter_by_tag(ALL_CASES, "login_failure")   # TC-AUTH-011 ~ 016
VALIDATION_CASES = _filter_by_tag(ALL_CASES, "validation")         # TC-AUTH-018 ~ 020
TOKEN_VERIFY_CASES = _filter_by_tag(ALL_CASES, "token_verify")     # TC-AUTH-021 ~ 023


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    """
    模块级 HTTP 客户端。
    base_url 和 timeout 来自 conftest.py 中的 session 级 fixture。
    scope=module 保证同一测试文件内复用同一个 client 实例。
    """
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def valid_token(client: ApiClient) -> str:
    """
    预先登录超级管理员，获取一个有效 token。
    用于 TC-AUTH-023（有效 Token 校验）的前置依赖。
    如果登录失败则跳过依赖此 fixture 的所有用例。
    """
    resp = client.request("POST", "/v1/token", json={
        "account": "super",
        "secret": "123456",
        "type": 100,
    })
    data = resp.json()
    token = _extract_token(data)
    if not token:
        pytest.skip("无法获取有效 token，跳过 token 校验用例")
    return token


# ---------------------------------------------------------------------------
# 请求执行器
# ---------------------------------------------------------------------------

def _execute_case(client: ApiClient, case: dict, token: Optional[str] = None) -> Any:
    """
    根据 YAML 用例字典构造并发送 HTTP 请求。

    参数：
      client: ApiClient 实例
      case:   单条 YAML 用例字典，包含 method / path / json / headers / params
      token:  可选的有效 token，用于替换 YAML 中的占位符 "{valid_token}"

    返回：
      requests.Response 对象
    """
    json_body = case.get("json", {}).copy()

    for key, val in json_body.items():
        if isinstance(val, str) and val == "{valid_token}" and token:
            json_body[key] = token

    return client.request(
        method=case.get("method", "POST"),
        path=case.get("path", "/v1/token"),
        json=json_body,
        headers=case.get("headers"),
        params=case.get("params"),
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


# ===========================================================================
# 测试函数：登录成功 (TC-AUTH-001 ~ TC-AUTH-010)
# 验证点：HTTP 200 + 响应中包含有效 token
# ===========================================================================

@pytest.mark.auth
@pytest.mark.parametrize(
    "case",
    LOGIN_SUCCESS_CASES,
    ids=[c["id"] for c in LOGIN_SUCCESS_CASES],
)
def test_login_success(client: ApiClient, case: dict):
    allure.dynamic.title(f"登录成功 - {case['id']}")
    allure.dynamic.feature("登录与鉴权")
    allure.dynamic.story("正常登录")
    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    if expected.get("has_token"):
        with allure.step("校验返回 token"):
            token = _extract_token(body)
            assert token, f"[{case['id']}] 响应中未包含 token: {body}"


# ===========================================================================
# 测试函数：登录失败 (TC-AUTH-011 ~ TC-AUTH-016)
# 验证点：返回业务错误（error_code != 0 或 HTTP 4xx）且不返回 token
# ===========================================================================

@pytest.mark.auth
@pytest.mark.parametrize(
    "case",
    LOGIN_FAILURE_CASES,
    ids=[c["id"] for c in LOGIN_FAILURE_CASES],
)
def test_login_failure(client: ApiClient, case: dict):
    allure.dynamic.title(f"登录失败 - {case['id']}")
    allure.dynamic.feature("登录与鉴权")
    allure.dynamic.story("异常登录")
    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if expected.get("error"):
        with allure.step("校验接口返回错误"):
            if resp.status_code == 200:
                assert _has_error(body), (
                    f"[{case['id']}] 业务应返回非零 error_code: {body}"
                )
            else:
                assert resp.status_code in (400, 401, 403, 404, 422), (
                    f"[{case['id']}] 期望 4xx 状态码, 实际 {resp.status_code}"
                )

    if expected.get("has_token") is False:
        with allure.step("校验失败场景不返回 token"):
            token = _extract_token(body)
            assert not token, f"[{case['id']}] 失败场景不应返回 token: {body}"


# ===========================================================================
# 测试函数：参数校验 (TC-AUTH-018 ~ TC-AUTH-020)
# 验证点：缺失/空值参数应被拦截，返回错误且不返回 token
# ===========================================================================

@pytest.mark.auth
@pytest.mark.parametrize(
    "case",
    VALIDATION_CASES,
    ids=[c["id"] for c in VALIDATION_CASES],
)
def test_param_validation(client: ApiClient, case: dict):
    allure.dynamic.title(f"参数校验 - {case['id']}")
    allure.dynamic.feature("登录与鉴权")
    allure.dynamic.story("参数校验")
    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if expected.get("error"):
        with allure.step("校验参数错误响应"):
            if resp.status_code == 200:
                assert _has_error(body), (
                    f"[{case['id']}] 参数校验应返回非零 error_code: {body}"
                )
            else:
                assert resp.status_code in (400, 401, 422), (
                    f"[{case['id']}] 期望 400/401/422, 实际 {resp.status_code}"
                )

    if expected.get("has_token") is False:
        with allure.step("校验参数错误不返回 token"):
            token = _extract_token(body)
            assert not token, f"[{case['id']}] 校验失败不应返回 token: {body}"


# ===========================================================================
# 测试函数：Token 校验失败 (TC-AUTH-021, TC-AUTH-022)
# 验证点：空 token / 伪造 token 应被拒绝
# ===========================================================================

@pytest.mark.auth
@pytest.mark.parametrize(
    "case",
    [c for c in TOKEN_VERIFY_CASES if c["id"] != "TC-AUTH-023"],
    ids=[c["id"] for c in TOKEN_VERIFY_CASES if c["id"] != "TC-AUTH-023"],
)
def test_token_verify_failure(client: ApiClient, case: dict):
    allure.dynamic.title(f"Token 校验失败 - {case['id']}")
    allure.dynamic.feature("登录与鉴权")
    allure.dynamic.story("Token 校验失败")
    resp = _execute_case(client, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if expected.get("error"):
        with allure.step("校验 token 失败响应"):
            if resp.status_code == 200:
                assert _has_error(body), (
                    f"[{case['id']}] 应返回校验失败: {body}"
                )
            else:
                assert resp.status_code in (400, 401, 422), (
                    f"[{case['id']}] 期望 4xx, 实际 {resp.status_code}"
                )


# ===========================================================================
# 测试函数：Token 校验成功 (TC-AUTH-023)
# 验证点：有效 token 应通过校验，返回 error_code=0
# 依赖 valid_token fixture 提供真实 token
# ===========================================================================

@pytest.mark.auth
def test_token_verify_success(client: ApiClient, valid_token: str):
    case = next((c for c in TOKEN_VERIFY_CASES if c["id"] == "TC-AUTH-023"), None)
    if not case:
        pytest.skip("未找到 TC-AUTH-023 用例")

    allure.dynamic.title(f"Token 校验成功 - {case['id']}")
    allure.dynamic.feature("登录与鉴权")
    allure.dynamic.story("Token 校验成功")
    resp = _execute_case(client, case, token=valid_token)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))

    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    expected_json = expected.get("json", {})
    with allure.step("校验响应字段"):
        for key, val in expected_json.items():
            assert body.get(key) == val, (
                f"期望 {key}={val}, 实际 {body.get(key)}"
            )
