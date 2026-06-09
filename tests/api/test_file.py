import pytest

from tests.common.api_client import ApiClient


@pytest.mark.smoke
@pytest.mark.file
def test_upload_placeholder(base_url, timeout):
    client = ApiClient(base_url, timeout=timeout)
    assert client.base_url.startswith("http")
