from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict

import pytest

from tests.common.api_client import ApiClient
from tests.common.auth_seed import get_test_tokens


@pytest.fixture(scope="session")
def integration_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def integration_client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="session")
def integration_tokens(integration_client: ApiClient) -> Dict[str, str]:
    return get_test_tokens(integration_client)


@pytest.fixture(scope="module")
def seed_users(integration_project_root):
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "users"], check=True)
    yield
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "users"], check=True)


@pytest.fixture(scope="module")
def seed_products(integration_project_root):
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "products"], check=True)
    yield
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "products"], check=True)


@pytest.fixture(scope="module")
def seed_orders(integration_project_root):
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "orders"], check=True)
    yield
    subprocess.run([sys.executable, str(integration_project_root / "fake.py"), "--scope", "orders"], check=True)
