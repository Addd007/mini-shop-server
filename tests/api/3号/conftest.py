import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import ensure_service, login_token, reset_data, stop_service


@pytest.fixture(scope="module")
def m3_environment(base_url):
    reset_data()
    process = ensure_service(base_url)
    yield
    stop_service(process)
    reset_data()


@pytest.fixture(scope="module")
def m3_tokens(base_url, timeout, m3_environment):
    return {
        "user": login_token(base_url, timeout, "user"),
        "super": login_token(base_url, timeout, "super"),
    }
