from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from support import execute, fetchall, fetchone

CASES = CaseLoader(Path(__file__).resolve().parents[2]).load("cases/3号/idempotency_cases.yaml")
C = {x["id"]: x for x in CASES}


def auth_client(base_url, timeout, token):
    return ApiClient(base_url, timeout, token)


def post_order(base_url, timeout, token, count=1):
    return auth_client(base_url,timeout,token).request("POST","/v1/order",
        json={"products":[{"product_id":1,"count":count}]})


def order_ids():
    return {x["id"] for x in fetchall("SELECT id FROM `order`")}


@pytest.fixture(autouse=True)
def clean_new_orders(m3_environment):
    before=order_ids(); yield
    new=order_ids()-before
    if new:
        marks=",".join(["%s"]*len(new)); vals=tuple(new)
        execute(f"DELETE FROM order_product WHERE order_id IN ({marks})",vals)
        execute(f"DELETE FROM `order` WHERE id IN ({marks})",vals)


@pytest.mark.idempotency
def test_sequential_duplicate_order(base_url, timeout, m3_tokens):
    case=C["TC-M3-IDEM-001"]; allure.dynamic.title(f"{case['id']} - {case['summary']}")
    responses=[post_order(base_url,timeout,m3_tokens["user"]) for _ in range(2)]
    ids=[(r.json().get("data") or {}).get("order_id") for r in responses if r.status_code==200]
    assert len(set(ids)) == 1, f"相同请求生成了多个订单: {ids}"


@pytest.mark.idempotency
def test_concurrent_duplicate_order(base_url, timeout, m3_tokens):
    case=C["TC-M3-IDEM-002"]; allure.dynamic.title(f"{case['id']} - {case['summary']}")
    with ThreadPoolExecutor(max_workers=5) as pool:
        responses=list(pool.map(lambda _: post_order(base_url,timeout,m3_tokens["user"]),range(5)))
    ids=[(r.json().get("data") or {}).get("order_id") for r in responses if r.status_code==200]
    assert len(set(ids)) == 1, f"并发相同请求生成了多个订单: {ids}"


@pytest.mark.idempotency
def test_order_numbers_unique(base_url, timeout, m3_tokens):
    case=C["TC-M3-IDEM-003"]; allure.dynamic.title(f"{case['id']} - {case['summary']}")
    responses=[post_order(base_url,timeout,m3_tokens["user"],i) for i in range(1,6)]
    numbers=[(r.json().get("data") or {}).get("order_no") for r in responses]
    assert all(numbers) and len(set(numbers)) == 5


@pytest.mark.idempotency
def test_failed_retries_leave_no_residue(base_url, timeout, m3_tokens):
    case=C["TC-M3-IDEM-004"]; allure.dynamic.title(f"{case['id']} - {case['summary']}")
    before_orders=fetchone("SELECT COUNT(*) n FROM `order`")["n"]
    before_rel=fetchone("SELECT COUNT(*) n FROM order_product")["n"]
    responses=[post_order(base_url,timeout,m3_tokens["user"],999) for _ in range(3)]
    assert all((r.json().get("data") or {}).get("pass") is False for r in responses)
    assert fetchone("SELECT COUNT(*) n FROM `order`")["n"] == before_orders
    assert fetchone("SELECT COUNT(*) n FROM order_product")["n"] == before_rel


@pytest.mark.idempotency
def test_repeated_payment_notify_is_idempotent(base_url, timeout, m3_tokens):
    case=C["TC-M3-IDEM-005"]; allure.dynamic.title(f"{case['id']} - {case['summary']}")
    client=auth_client(base_url,timeout,m3_tokens["user"])
    payload={"order_id":1,"transaction_id":"M3-SAME-NOTIFY","amount":"0.20"}
    responses=[client.request("POST","/v1/pay/notify",json=payload) for _ in range(2)]
    assert all(r.status_code == 200 for r in responses), [(r.status_code,r.text) for r in responses]
