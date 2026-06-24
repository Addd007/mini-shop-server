from __future__ import annotations

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.integration.utils import attach_case, get_auth_client, load_cases


CASES = load_cases(__file__, "order_cases.yaml")


@pytest.fixture(scope="module", autouse=True)
def seed_order_data(seed_orders):
    yield


@pytest.fixture(scope="module")
def user_client(integration_client: ApiClient, integration_tokens) -> ApiClient:
    return get_auth_client(integration_client, integration_tokens["user"])


@pytest.fixture(scope="module")
def super_client(integration_client: ApiClient, integration_tokens) -> ApiClient:
    return get_auth_client(integration_client, integration_tokens["super"])


@pytest.fixture(scope="module")
def anon_client(integration_client: ApiClient) -> ApiClient:
    return integration_client


@pytest.fixture(scope="module")
def order_product_id(super_client: ApiClient) -> int:
    payload = {
        "name": "订单测试商品",
        "category_id": 1,
        "main_img_url": "http://example.com/order-product.jpg",
        "price": 19.9,
        "stock": 50,
        "summary": "订单流转用商品",
    }
    create_resp = super_client.request("POST", "/v1/product", json=payload)
    attach_case("ORDER-SETUP-CREATE-PRODUCT", create_resp, payload)
    assert create_resp.status_code in (200, 201)

    recent_resp = super_client.request("GET", "/v1/product/recent", params={"count": 5})
    attach_case("ORDER-SETUP-RECENT-PRODUCT", recent_resp, {"count": 5})
    recent_body = recent_resp.json() or {}
    recent_data = recent_body.get("data") or []
    product_id = None
    if isinstance(recent_data, list) and recent_data:
        first = recent_data[0]
        if isinstance(first, dict):
            product_id = first.get("id") or first.get("product_id")
    if not product_id:
        list_resp = super_client.request("GET", "/v1/product/list/by_category", params={"category_id": 1, "page": 1, "size": 10})
        attach_case("ORDER-SETUP-PRODUCT-LIST", list_resp, {"category_id": 1})
        list_body = list_resp.json() or {}
        list_data = list_body.get("data") or []
        if isinstance(list_data, list) and list_data:
            first = list_data[0]
            if isinstance(first, dict):
                product_id = first.get("id") or first.get("product_id")
    assert product_id, f"创建订单商品失败，响应未返回可用商品ID: recent={recent_body}"
    yield product_id
    super_client.request("DELETE", f"/v1/product/{product_id}")


@pytest.mark.integration
@pytest.mark.order
def test_order_flow_place_list_detail(user_client: ApiClient, anon_client: ApiClient, order_product_id: int):
    allure.dynamic.title("订单下单、列表、详情闭环")

    place_case = next(c for c in CASES if c["id"] == "ORDER-SC-001")
    place_payload = {"products": [{"product_id": order_product_id, "count": 1}]}
    place_resp = user_client.request(method=place_case["method"], path=place_case["path"], json=place_payload)
    attach_case(place_case["id"], place_resp, place_payload)
    assert place_resp.status_code == place_case["expected"]["status_code"]
    place_body = place_resp.json() or {}
    order_data = place_body.get("data") or {}
    order_id = order_data.get("order_id") or order_data.get("id") or place_body.get("order_id") or place_body.get("id")
    assert order_id, f"订单提交成功但未返回订单 ID: {place_body}"

    list_case = next(c for c in CASES if c["id"] == "ORDER-SC-002")
    list_resp = user_client.request(method=list_case["method"], path=list_case["path"], params=list_case.get("params"))
    attach_case(list_case["id"], list_resp, list_case.get("params"))
    assert list_resp.status_code == list_case["expected"]["status_code"]

    detail_case = next(c for c in CASES if c["id"] == "ORDER-SC-003")
    detail_resp = user_client.request(method=detail_case["method"], path=f"/v1/order/{order_id}")
    attach_case(detail_case["id"], detail_resp, {"order_id": order_id})
    assert detail_resp.status_code in (detail_case["expected"]["status_code"], 403, 404)


@pytest.mark.integration
@pytest.mark.order
def test_order_validation_and_auth(user_client: ApiClient, anon_client: ApiClient):
    allure.dynamic.title("订单参数校验与未登录拦截")

    invalid_case = next(c for c in CASES if c["id"] == "ORDER-SC-004")
    invalid_resp = user_client.request(method=invalid_case["method"], path=invalid_case["path"], json=invalid_case["json"])
    attach_case(invalid_case["id"], invalid_resp, invalid_case["json"])
    assert invalid_resp.status_code == invalid_case["expected"]["status_code"]

    anon_resp = anon_client.request("GET", "/v1/order", params={"page": 1, "size": 10})
    attach_case("ORDER-ANON-LIST", anon_resp, {"page": 1, "size": 10})
    assert anon_resp.status_code == 401