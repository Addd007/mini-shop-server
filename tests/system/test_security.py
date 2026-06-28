"""
System Test A - Security tests for member 3.

Covered scenarios:
  S-04: SQL injection attempts
  S-05: token tampering
  S-06: horizontal privilege escalation on order detail
  S-07: unauthorized CMS access
  S-08: illegal file upload type

Run:
  pytest tests/system/test_security.py -v -m security
"""

from __future__ import annotations

import io
from typing import Any

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.system.conftest import _fetchone


def _json_or_empty(resp) -> dict[str, Any]:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


def _has_token(body: dict[str, Any]) -> bool:
    return bool(body.get("token") or body.get("data", {}).get("token"))


@pytest.mark.security
@pytest.mark.parametrize(
    "payload",
    [
        {"account": "' OR 1=1--", "secret": "anything", "type": 100},
        {"account": "user' OR '1'='1", "secret": "wrong-password", "type": 100},
        {"account": "user'; DROP TABLE user; --", "secret": "123456", "type": 100},
        {"account": "admin') OR ('1'='1", "secret": "' OR '1'='1", "type": 100},
    ],
    ids=["or_true_comment", "or_true_password", "drop_table", "balanced_quote"],
)
def test_s04_sql_injection_login_rejected(base_url, timeout, ensure_running, payload):
    """S-04: SQL injection payloads must not bypass login or damage data."""
    allure.dynamic.title(f"S-04 SQL injection rejected: {payload['account']}")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-04 SQL injection")

    client = ApiClient(base_url, timeout)
    resp = client.request("POST", "/v1/token", json=payload)
    body = _json_or_empty(resp)

    allure.attach(str(payload), name="injection_payload", attachment_type=allure.attachment_type.TEXT)
    allure.attach(f"status={resp.status_code}\nbody={resp.text[:500]}", name="response", attachment_type=allure.attachment_type.TEXT)

    user_count = _fetchone("SELECT COUNT(*) AS cnt FROM user")["cnt"]
    assert user_count > 0, "user table should still exist and contain baseline data"
    assert not (resp.status_code == 200 and _has_token(body)), (
        f"SQL injection appears to have bypassed login: status={resp.status_code}, body={body}"
    )
    assert resp.status_code != 500, f"SQL injection should be handled gracefully, got 500: {resp.text[:300]}"


@pytest.mark.security
def test_s04_sql_injection_path_parameter_rejected(base_url, timeout, ensure_running):
    """S-04: SQL-like product id path must be rejected by parameter validation."""
    allure.dynamic.title("S-04 SQL-like product id rejected")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-04 SQL injection")

    client = ApiClient(base_url, timeout)
    resp = client.request("GET", "/v1/product/1 OR 1=1")
    allure.attach(f"status={resp.status_code}\nbody={resp.text[:500]}", name="response", attachment_type=allure.attachment_type.TEXT)

    assert resp.status_code in (400, 404, 422), (
        f"SQL-like id should be rejected as bad path/parameter, got {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.security
def test_s05_token_tampering_rejected(base_url, timeout, tokens):
    """S-05: a modified token cannot access protected APIs."""
    allure.dynamic.title("S-05 Token tampering rejected")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-05 token tampering")

    original = tokens["user"]
    middle = len(original) // 2
    replacement = "A" if original[middle] != "A" else "B"
    tampered = original[:middle] + replacement + original[middle + 1 :]

    client = ApiClient(base_url, timeout, token=tampered)
    resp = client.request("GET", "/v1/user")
    allure.attach(f"status={resp.status_code}\nbody={resp.text[:500]}", name="tampered_token_response", attachment_type=allure.attachment_type.TEXT)

    assert resp.status_code in (401, 403), (
        f"Tampered token should be rejected, got {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.security
def test_s05_random_token_rejected(base_url, timeout, ensure_running):
    """S-05: a forged random token cannot access protected APIs."""
    allure.dynamic.title("S-05 Forged random token rejected")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-05 token tampering")

    client = ApiClient(base_url, timeout, token="forged.invalid.token")
    resp = client.request("GET", "/v1/user")
    allure.attach(f"status={resp.status_code}\nbody={resp.text[:500]}", name="forged_token_response", attachment_type=allure.attachment_type.TEXT)

    assert resp.status_code in (401, 403), (
        f"Forged token should be rejected, got {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.security
def test_s06_horizontal_order_access_rejected(base_url, timeout, tokens):
    """S-06: user token cannot read another user's order detail."""
    allure.dynamic.title("S-06 Horizontal privilege escalation rejected")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-06 horizontal privilege escalation")

    current_user = _fetchone(
        "SELECT u.id FROM user u "
        "JOIN identity i ON i.user_id = u.id "
        "WHERE i.identifier=%s AND i.type=100 LIMIT 1",
        ("user",),
    )
    if current_user is None:
        current_user = _fetchone("SELECT id FROM user WHERE nickname=%s LIMIT 1", ("user",))
    assert current_user is not None, "baseline user account should exist"

    other_order = _fetchone(
        "SELECT id, user_id FROM `order` WHERE user_id <> %s ORDER BY id LIMIT 1",
        (current_user["id"],),
    )
    assert other_order is not None, "baseline should contain at least one order from another user"

    client = ApiClient(base_url, timeout, token=tokens["user"])
    resp = client.request("GET", f"/v1/order/{other_order['id']}")
    allure.attach(
        f"current_user={current_user['id']}, target_order={other_order}\n"
        f"status={resp.status_code}\nbody={resp.text[:500]}",
        name="horizontal_access_response",
        attachment_type=allure.attachment_type.TEXT,
    )

    assert resp.status_code in (401, 403, 404), (
        f"User {current_user['id']} can read order {other_order['id']} of user {other_order['user_id']}: "
        f"{resp.status_code} {resp.text[:300]}"
    )


@pytest.mark.security
@pytest.mark.parametrize(
    "path,params",
    [
        ("/cms/group/all", None),
        ("/cms/admin/list", {"page": 1, "size": 10, "group_id": 1}),
        ("/cms/order/list", {"page": 1, "size": 10}),
        ("/cms/file/list", {"parent_id": 0, "page": 1, "size": 10}),
    ],
    ids=["group_all", "admin_list", "order_list", "file_list"],
)
def test_s07_cms_unauthorized_access_rejected(base_url, timeout, tokens, path, params):
    """S-07: normal user must not access CMS management APIs."""
    allure.dynamic.title(f"S-07 CMS unauthorized access rejected: {path}")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-07 CMS unauthorized access")

    client = ApiClient(base_url, timeout, token=tokens["user"])
    resp = client.request("GET", path, params=params)
    allure.attach(f"path={path}, params={params}\nstatus={resp.status_code}\nbody={resp.text[:500]}", name="cms_response", attachment_type=allure.attachment_type.TEXT)

    assert resp.status_code in (401, 403), (
        f"Normal user should not access CMS management API {path}, got {resp.status_code}: {resp.text[:300]}"
    )


@pytest.mark.security
@pytest.mark.parametrize(
    "filename,content_type",
    [
        ("shell.php", "application/x-php"),
        ("webshell.jsp", "application/octet-stream"),
        ("empty.exe", "application/octet-stream"),
    ],
    ids=["php", "jsp", "exe"],
)
def test_s08_illegal_file_upload_type_rejected(base_url, timeout, tokens, filename, content_type):
    """S-08: illegal executable/server-side file types must be rejected."""
    allure.dynamic.title(f"S-08 Illegal file upload rejected: {filename}")
    allure.dynamic.feature("System Test A - Security")
    allure.dynamic.story("S-08 illegal file upload")

    client = ApiClient(base_url, timeout, token=tokens["super"])
    file_bytes = io.BytesIO(b"<?php echo 'unsafe'; ?>" if filename.endswith(".php") else b"unsafe-test-content")
    resp = client.request(
        "POST",
        "/cms/file/0",
        files={"file": (filename, file_bytes, content_type)},
    )
    body = _json_or_empty(resp)
    allure.attach(f"status={resp.status_code}\nbody={resp.text[:500]}", name="upload_response", attachment_type=allure.attachment_type.TEXT)

    success_with_file = resp.status_code == 200 and body.get("error_code") in (0, 1)
    assert not success_with_file, (
        f"Illegal file type {filename} should be rejected, got {resp.status_code}: {resp.text[:300]}"
    )
    assert resp.status_code in (400, 401, 403, 413, 415, 422, 500), (
        f"Illegal upload should return an error status, got {resp.status_code}: {resp.text[:300]}"
    )
