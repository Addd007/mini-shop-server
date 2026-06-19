"""
4号测试团队 — 共享 Fixtures 和初始化

提供：
  - initialize_module : 模块级自动初始化（fake.py --scope users）
  - client            : 未认证的 ApiClient
  - auth_client       : 已认证的 ApiClient（super/123456）

各测试文件可直接使用 client / auth_client，无需重复定义。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from tests.common.api_client import ApiClient

# ---------------------------------------------------------------------------
# 模块初始化（自动执行）
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module", autouse=True)
def initialize_module():
    """每个测试模块启动前自动初始化测试数据。

    执行 fake.py --scope users 来准备基础用户/数据。
    如果 fake.py 不可用或失败，不会阻塞测试执行。
    teardown 阶段不做额外清理，由各模块负责清理自身产生的文件。
    """
    project_root = Path(__file__).resolve().parents[3]
    fake_script = project_root / "fake.py"
    if fake_script.exists():
        result = subprocess.run(
            [sys.executable, str(fake_script), "--scope", "users"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"[WARNING] fake.py 初始化失败 (exit {result.returncode}): {result.stderr[:200]}")
    else:
        print("[WARNING] fake.py 不存在，跳过数据初始化")
    yield


# ---------------------------------------------------------------------------
# 基础客户端
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    """未认证的客户端"""
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def auth_client(base_url, timeout) -> ApiClient:
    """已认证的管理员客户端。

    使用 super/123456 获取 Token，认证方式为 HTTP Basic Auth
    （username=token, password=132），与 Postman 一致。
    """
    client = ApiClient(base_url=base_url, timeout=timeout)
    resp = client.request("POST", "/v1/token", json={
        "account": "super",
        "secret": "123456",
        "type": 100,
    })
    data = resp.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        pytest.skip("无法获取 Token，跳过需要认证的测试")
    return ApiClient(base_url=base_url, timeout=timeout, token=token)
