from __future__ import annotations

from typing import Dict, Iterable, Tuple

from tests.common.api_client import ApiClient

DEFAULT_TEST_ACCOUNTS: tuple[Tuple[str, str, str], ...] = (
    ("super", "super", "123456"),
    ("admin", "admin", "123456"),
    ("user", "user", "123456"),
    ("Allen3D", "Allen3D", "123456"),
)


def get_test_tokens(client: ApiClient, accounts: Iterable[Tuple[str, str, str]] = DEFAULT_TEST_ACCOUNTS) -> Dict[str, str]:
    """登录预置账号并返回 token 映射。"""
    result: Dict[str, str] = {}
    for name, account, secret in accounts:
        resp = client.request(
            "POST",
            "/v1/token",
            json={"account": account, "secret": secret, "type": 100},
        )
        data = resp.json()
        token = data.get("token") or data.get("data", {}).get("token")
        if token:
            result[name] = token
    return result
