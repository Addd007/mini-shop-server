import pytest

from tests.common.api_client import ApiClient


@pytest.mark.smoke
def test_health_like_homepage(base_url, timeout):
    client = ApiClient(base_url, timeout=timeout)
    response = client.request("GET", "/")
    assert response.status_code < 500
