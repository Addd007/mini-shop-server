"""
用户接口自动化测试

测试依据：test_cases/1号/user.md
数据来源：tests/cases/user/user_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化测试账号

测试分组（按 YAML 中的 tag 字段划分）：
  - user_info       : 用户信息查询（TC-USER-001 ~ 002）
  - user_auths      : 权限查询（TC-USER-003 ~ 004）
  - avatar          : 头像修改（TC-USER-005）
  - password        : 密码修改（TC-USER-006 ~ 013）
  - profile         : 资料修改（TC-USER-014 ~ 015）
  - profile_conflict: 资料重复校验（TC-USER-016 ~ 018）
  
  - unbind          : 账号解绑（TC-USER-019 ~ 021）
  - bind            : 账号绑定（TC-USER-022 ~ 027）
  - delete_account  : 注销账号（TC-USER-028）
  - register_reuse  : 删除后复用注册（TC-USER-029 ~ 030）

运行方式：
  pytest tests/api/test_user_cases.py -v              # 全量运行
  pytest tests/api/test_user_cases.py -k TC-USER-001  # 按用例 ID 筛选
  pytest -m user -v                                   # 按 marker 筛选
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import subprocess
import sys

import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


CASE_FILE = "cases/user/user_cases.yaml"


def _load_cases() -> list[dict[str, Any]]:
    """从 YAML 文件加载全部测试用例"""
    loader = CaseLoader(Path(__file__).resolve().parents[1])
    return loader.load(CASE_FILE)


@pytest.fixture(scope="session", autouse=True)
def initialize_test_data():
    """每轮测试前重建基础测试数据。"""
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "fake.py")], check=True)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    """按 tag 字段过滤用例"""
    return [c for c in cases if c.get("tag") == tag]


def _extract_token(resp_json: dict) -> Optional[str]:
    """从响应 JSON 中提取 token"""
    return resp_json.get("token") or resp_json.get("data", {}).get("token")


def _has_error(resp_json: dict) -> bool:
    """判断响应 JSON 是否包含业务错误（error_code 非零）"""
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


ALL_CASES = _load_cases()
USER_INFO_CASES = _filter_by_tag(ALL_CASES, "user_info")
USER_AUTHS_CASES = _filter_by_tag(ALL_CASES, "user_auths")
AVATAR_CASES = _filter_by_tag(ALL_CASES, "avatar")
PASSWORD_CASES = _filter_by_tag(ALL_CASES, "password")
PROFILE_CASES = _filter_by_tag(ALL_CASES, "profile")
PROFILE_CONFLICT_CASES = _filter_by_tag(ALL_CASES, "profile_conflict")
BIND_CASES = _filter_by_tag(ALL_CASES, "bind")
UNBIND_CASES = _filter_by_tag(ALL_CASES, "unbind")
DELETE_ACCOUNT_CASES = _filter_by_tag(ALL_CASES, "delete_account")
REGISTER_REUSE_CASES = _filter_by_tag(ALL_CASES, "register_reuse")


REUSE_SEED = {
    "username": "user",
    "mobile": "19900000003",
    "email": "111@qq.com",
    "password": "123456",
}


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    """模块级 HTTP 客户端"""
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    """
    预先登录多个测试账号，获取各自的 token。
    返回字典：{"super": token, "admin": token, "user": token}
    """
    accounts = [
        ("super", "super", "123456"),
        ("admin", "admin", "123456"),
        ("user", "user", "123456"),
    ]
    result = {}
    for name, account, secret in accounts:
        resp = client.request("POST", "/v1/token", json={
            "account": account,
            "secret": secret,
            "type": 100,
        })
        data = resp.json()
        token = _extract_token(data)
        if token:
            result[name] = token
    return result


def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    """
    根据用例的 auth 字段返回带对应 token 的客户端。
    auth 可选值：super / admin / user / none
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
    path = case.get("path", "/v1/user")
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


# ===========================================================================
# 用户信息查询 (TC-USER-001 ~ TC-USER-002)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    USER_INFO_CASES,
    ids=[c["id"] for c in USER_INFO_CASES],
)
def test_user_info(client: ApiClient, tokens: Dict[str, str], case: dict):
    """用户信息查询：验证登录态和返回字段"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()

    if expected.get("error"):
        _assert_error_response(case, resp, body)
    else:
        if "status_code" in expected:
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )
        if "has_fields" in expected:
            for field in expected["has_fields"]:
                assert field in body or field in body.get("data", {}), (
                    f"[{case['id']}] 响应缺少字段 {field}: {body}"
                )


# ===========================================================================
# 权限查询 (TC-USER-003 ~ TC-USER-004)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    USER_AUTHS_CASES,
    ids=[c["id"] for c in USER_AUTHS_CASES],
)
def test_user_auths(client: ApiClient, tokens: Dict[str, str], case: dict):
    """权限查询：验证不同角色的权限列表"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 头像修改 (TC-USER-005)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    AVATAR_CASES,
    ids=[c["id"] for c in AVATAR_CASES],
)
def test_avatar_update(client: ApiClient, tokens: Dict[str, str], case: dict):
    """头像修改：验证头像 URL 更新"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 密码修改 (TC-USER-006 ~ TC-USER-013)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    PASSWORD_CASES,
    ids=[c["id"] for c in PASSWORD_CASES],
)
def test_password_change(client: ApiClient, tokens: Dict[str, str], case: dict):
    """
    密码修改：验证密码规则校验和修改逻辑。
    注意：部分用例会真正修改密码，可能影响后续测试，需要 teardown 恢复。
    """
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()

    if expected.get("error"):
        _assert_error_response(case, resp, body)
    else:
        if "status_code" in expected:
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

    # 如果修改成功且有 teardown 标记，需要恢复密码
    if case.get("teardown") == "reset_user_password" and resp.status_code in (200, 201):
        new_pwd = case["json"]["new_password"]
        _reset_password(client, tokens, "user", new_pwd, "123456")


def _reset_password(client: ApiClient, tokens: Dict[str, str], user: str, old_pwd: str, new_pwd: str):
    """辅助函数：恢复用户密码"""
    resp = client.request("POST", "/v1/token", json={
        "account": user,
        "secret": old_pwd,
        "type": 100,
    })
    data = resp.json()
    token = _extract_token(data)
    if not token:
        return

    temp_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)
    temp_client.request("PUT", "/v1/user/password", json={
        "old_password": old_pwd,
        "new_password": new_pwd,
        "confirm_password": new_pwd,
    })
    tokens[user] = token


def _ensure_reuse_seed_deleted(client: ApiClient):
    """确保复用测试的种子账号处于已删除状态。"""
    temp_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    token_resp = temp_client.request("POST", "/v1/token", json={
        "account": REUSE_SEED["username"],
        "secret": REUSE_SEED["password"],
        "type": 100,
    })
    token = _extract_token(token_resp.json())
    if not token:
        return
    auth_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)
    auth_client.request("DELETE", "/v1/user")


def _delete_reused_account(client: ApiClient, case: dict):
    """将删除后复用的账号再次软删除，保持复用测试可重复执行。"""
    auth = case.get("auth", "none")
    if auth != "none":
        return
    temp_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    token_resp = temp_client.request("POST", "/v1/token", json={
        "account": case["json"]["username"],
        "secret": case["json"]["password"],
        "type": 100,
    })
    token = _extract_token(token_resp.json())
    if not token:
        return
    auth_client = ApiClient(base_url=client.base_url, timeout=client.timeout, token=token)
    auth_client.request("DELETE", "/v1/user")


# ===========================================================================
# 资料修改 (TC-USER-014 ~ TC-USER-015)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    PROFILE_CASES,
    ids=[c["id"] for c in PROFILE_CASES],
)
def test_profile_update(client: ApiClient, tokens: Dict[str, str], case: dict):
    """资料修改：验证用户资料更新"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 资料重复校验 (TC-USER-016 ~ TC-USER-018)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    PROFILE_CONFLICT_CASES,
    ids=[c["id"] for c in PROFILE_CONFLICT_CASES],
)
def test_profile_conflict(client: ApiClient, tokens: Dict[str, str], case: dict):
    """资料重复校验：用户名/手机号/邮箱已被占用时应返回错误"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()

    if expected.get("error"):
        _assert_error_response(case, resp, body)





# ===========================================================================
# 账号解绑 (TC-USER-020 ~ TC-USER-023)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    UNBIND_CASES,
    ids=[c["id"] for c in UNBIND_CASES],
)
def test_account_unbind(client: ApiClient, tokens: Dict[str, str], case: dict):
    """账号解绑：验证解绑逻辑"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()

    if expected.get("error"):
        _assert_error_response(case, resp, body)
    else:
        if "status_code" in expected:
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
            )

# ===========================================================================
# 账号绑定 (TC-USER-024 ~ TC-USER-027)
# ===========================================================================

@pytest.mark.user
@pytest.mark.parametrize(
    "case",
    BIND_CASES,
    ids=[c["id"] for c in BIND_CASES],
)
def test_account_bind(client: ApiClient, tokens: Dict[str, str], case: dict):
    """账号绑定：验证重复绑定和已占用账号的错误处理"""
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()

    if expected.get("error"):
        _assert_error_response(case, resp, body)


# ===========================================================================
# 注销账号 (TC-USER-028)
# ===========================================================================

@pytest.mark.user
@pytest.mark.delete_account
@pytest.mark.parametrize(
    "case",
    DELETE_ACCOUNT_CASES,
    ids=[c["id"] for c in DELETE_ACCOUNT_CASES],
)
def test_delete_account(client: ApiClient, tokens: Dict[str, str], case: dict):
    """
    注销账号：验证账号删除功能。
    警告：此测试会真正删除 user 账号，执行前先重新初始化测试数据。
    """
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[2] / "fake.py")], check=True)
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})

    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )


# ===========================================================================
# 删除后复用注册 (TC-USER-029 ~ TC-USER-030)
# ===========================================================================

@pytest.mark.user
@pytest.mark.register_reuse
@pytest.mark.parametrize(
    "case",
    REGISTER_REUSE_CASES,
    ids=[c["id"] for c in REGISTER_REUSE_CASES],
)
def test_register_reuse(client: ApiClient, case: dict):
    """删除后复用注册：验证用户名+手机号/邮箱命中已删除账号时可复用。"""
    _ensure_reuse_seed_deleted(client)
    resp = client.request(
        method=case.get("method", "POST"),
        path=case.get("path", "/v1/user"),
        json=case.get("json") if case.get("json") else None,
    )
    expected = case.get("expected", {})
    body = resp.json()

    if "status_code" in expected:
        assert resp.status_code == expected["status_code"], (
            f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}"
        )
    if expected.get("error"):
        _assert_error_response(case, resp, body)
    elif resp.status_code in (200, 201):
        _delete_reused_account(client, case)
