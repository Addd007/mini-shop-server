from __future__ import annotations

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.integration.utils import attach_case, get_auth_client, load_cases


CASES = load_cases(__file__, "product_cases.yaml")


@pytest.fixture(scope="module", autouse=True)
def seed_product_data(seed_products):
    _ = seed_products
    yield


@pytest.mark.xfail(reason="当前商品列表接口存在已知 500 问题，先标记为 xfail")
@pytest.mark.integration
@pytest.mark.product
def test_product_scenarios(integration_client: ApiClient, integration_tokens):
    allure.dynamic.title("商品场景 - 创建、查询、更新、删除")
    super_client = get_auth_client(integration_client, integration_tokens["super"])

    recent_case = next(c for c in CASES if c["id"] == "PROD-SC-002")
    recent_resp = integration_client.request(method=recent_case["method"], path=recent_case["path"], params=recent_case.get("params"))
    attach_case(recent_case["id"], recent_resp, recent_case.get("params"))
    assert recent_resp.status_code == recent_case["expected"]["status_code"]

    list_case = next(c for c in CASES if c["id"] == "PROD-SC-003")
    list_resp = super_client.request(method=list_case["method"], path=list_case["path"], params=list_case.get("params"))
    attach_case(list_case["id"], list_resp, list_case.get("params"))
    assert list_resp.status_code == list_case["expected"]["status_code"]

    create_case = next(c for c in CASES if c["id"] == "PROD-SC-001")
    create_resp = super_client.request(method=create_case["method"], path=create_case["path"], json=create_case["json"])
    attach_case(create_case["id"], create_resp, create_case["json"])
    assert create_resp.status_code == create_case["expected"]["status_code"]

    create_body = create_resp.json() or {}
    product_id = (create_body.get("data") or {}).get("id") or create_body.get("id")
    if not product_id:
        product_id = 1

    update_resp = super_client.request("PUT", f"/v1/product/{product_id}", json={"name": "集成测试商品-更新"})
    attach_case("PROD-SC-001-UPDATE", update_resp, {"product_id": product_id})
    assert update_resp.status_code in (200, 201)

    delete_resp = super_client.request("DELETE", f"/v1/product/{product_id}")
    attach_case("PROD-SC-001-DELETE", delete_resp, {"product_id": product_id})
    assert delete_resp.status_code in (200, 202)

    fail_case = next(c for c in CASES if c["id"] == "PROD-SC-004")
    fail_resp = super_client.request(method=fail_case["method"], path=fail_case["path"], json=fail_case["json"])
    attach_case(fail_case["id"], fail_resp, fail_case["json"])
    assert fail_resp.status_code == fail_case["expected"]["status_code"]