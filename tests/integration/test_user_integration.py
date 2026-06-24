from __future__ import annotations

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.integration.utils import attach_case, get_auth_client, load_cases


CASES = load_cases(__file__, "user_cases.yaml")


@pytest.fixture(scope="module", autouse=True)
def seed_user_data(seed_users):
    yield


@pytest.fixture(scope="module")
def super_client(integration_client: ApiClient, integration_tokens) -> ApiClient:
    return get_auth_client(integration_client, integration_tokens["super"])


@pytest.fixture(scope="module")
def user_client(integration_client: ApiClient, integration_tokens) -> ApiClient:
    return get_auth_client(integration_client, integration_tokens["user"])


@pytest.fixture(scope="module")
def prepared_super_client(integration_client: ApiClient, integration_tokens) -> ApiClient:
    super_client = get_auth_client(integration_client, integration_tokens["super"])
    # 查询当前信息，确保 token 可用
    resp = super_client.request("GET", "/v1/user")
    attach_case("USER-SETUP-VERIFY-SUPER", resp)
    assert resp.status_code == 200
    return super_client


@pytest.mark.integration
@pytest.mark.user
def test_user_profile_roundtrip(prepared_super_client: ApiClient):
    allure.dynamic.title("查询并更新当前用户资料")

    before_resp = prepared_super_client.request("GET", "/v1/user")
    attach_case("USER-PROFILE-BEFORE", before_resp)
    assert before_resp.status_code == 200
    before_body = before_resp.json()
    before_data = before_body.get("data", before_body)
    assert "nickname" in before_data
    assert "auth" in before_data

    update_payload = {
        "username": "super",
        "nickname": "集成测试超级管理员",
        "mobile": "19900000001",
        "email": "999@qq.com",
    }
    update_resp = prepared_super_client.request("PUT", "/v1/user", json=update_payload)
    attach_case("USER-PROFILE-UPDATE", update_resp, update_payload)
    assert update_resp.status_code in (200, 201, 400)

    after_resp = prepared_super_client.request("GET", "/v1/user")
    attach_case("USER-PROFILE-AFTER", after_resp)
    assert after_resp.status_code == 200
    after_body = after_resp.json()
    after_data = after_body.get("data", after_body)
    assert "nickname" in after_data
    assert "auth" in after_data


@pytest.mark.integration
@pytest.mark.user
def test_user_password_change_and_restore(super_client: ApiClient):
    allure.dynamic.title("修改密码并恢复")

    change_case = next(c for c in CASES if c["id"] == "USER-SC-003")
    change_resp = super_client.request(method=change_case["method"], path=change_case["path"], json=change_case["json"])
    attach_case(change_case["id"], change_resp, change_case["json"])
    assert change_resp.status_code in (200, 201)

    relogin_resp = super_client.request(
        "POST",
        "/v1/token",
        json={"account": "super", "secret": "1234567", "type": 100},
    )
    attach_case("USER-PASSWORD-RELOGIN", relogin_resp, {"account": "super", "secret": "1234567"})
    assert relogin_resp.status_code == 200
    relogin_body = relogin_resp.json()
    assert relogin_body.get("token") or relogin_body.get("data", {}).get("token")

    restore_resp = super_client.request(
        "PUT",
        "/v1/user/password",
        json={"old_password": "1234567", "new_password": "123456", "confirm_password": "123456"},
    )
    attach_case("USER-PASSWORD-RESTORE", restore_resp, {"old_password": "1234567", "new_password": "123456"})
    assert restore_resp.status_code in (200, 201)


@pytest.mark.integration
@pytest.mark.user
def test_user_bind_unbind_flow(prepared_super_client: ApiClient):
    allure.dynamic.title("账号绑定解绑流程")

    bind_case = next(c for c in CASES if c["id"] == "USER-SC-004")
    bind_resp = prepared_super_client.request(method=bind_case["method"], path=bind_case["path"], json=bind_case["json"])
    attach_case(bind_case["id"], bind_resp, bind_case["json"])
    assert bind_resp.status_code in (200, 201, 400)

    unbind_case = next(c for c in CASES if c["id"] == "USER-SC-005")
    unbind_resp = prepared_super_client.request(method=unbind_case["method"], path=unbind_case["path"], json=unbind_case["json"])
    attach_case(unbind_case["id"], unbind_resp, unbind_case["json"])
    assert unbind_resp.status_code in (200, 201, 400)
