"""
2号测试夹具：CMS 数据初始化与模块隔离

- initialize_cms_data : 会话级，测试启动前一次性重建 CMS 种子数据
- isolate_cms_module   : 模块级，每个测试模块前后各重置一次 CMS 数据
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


FAKE_PATH = Path(__file__).resolve().parents[3] / "fake.py"


@pytest.fixture(scope="session", autouse=True)
def initialize_cms_data():
    """测试会话启动前重建 CMS 种子数据（route/menu/group/auth/config/dict/notice/oper_log）。"""
    subprocess.run(
        [sys.executable, str(FAKE_PATH), "--scope", "cms"],
        check=True,
    )


@pytest.fixture(scope="module", autouse=True)
def isolate_cms_module():
    """每个 CMS 测试模块前后各重置一次数据，保证模块间用例隔离。"""
    subprocess.run(
        [sys.executable, str(FAKE_PATH), "--scope", "cms"],
        check=True,
    )
    yield
    subprocess.run(
        [sys.executable, str(FAKE_PATH), "--scope", "cms"],
        check=True,
    )
