import pytest

from tests.common.api_client import ApiClient
from tests.common.token_manager import TokenManager


@pytest.mark.smoke
@pytest.mark.auth
def test_login_success(base_url, test_user, timeout):
    manager = TokenManager(base_url, timeout=timeout)
    token = manager.login(test_user["username"], test_user["password"])
    assert token


@pytest.mark.smoke
@pytest.mark.auth
def test_login_failure(base_url, test_user, timeout):
    client = ApiClient(base_url, timeout=timeout)
    response = client.request(
        "POST",
        "/v1/token",
        json={"username": test_user["username"], "password": "wrong-password"},
    )
    assert response.status_code in (400, 401, 403)
