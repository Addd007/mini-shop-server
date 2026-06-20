"""成员三：订单库存、金额、快照与数据一致性自动化测试。"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path
from typing import Any

import allure
import pymysql
import pytest
import requests
from sqlalchemy.engine import make_url

from app.config.secure import SQLALCHEMY_DATABASE_URI
from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader


ROOT_DIR = Path(__file__).resolve().parents[3]
CASE_FILE = "cases/3号/order_business_cases.yaml"
CASES = CaseLoader(Path(__file__).resolve().parents[2]).load(CASE_FILE)
CASE_BY_ID = {case["id"]: case for case in CASES}
DB_URL = make_url(SQLALCHEMY_DATABASE_URI)


def _db_connect():
    return pymysql.connect(
        host=DB_URL.host,
        port=DB_URL.port or 3306,
        user=DB_URL.username,
        password=DB_URL.password,
        database=DB_URL.database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )


def _fetchone(sql: str, params: tuple = ()) -> dict | None:
    with _db_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()


def _fetchall(sql: str, params: tuple = ()) -> list[dict]:
    with _db_connect() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())


def _execute(sql: str, params: tuple = ()) -> int:
    with _db_connect() as conn:
        with conn.cursor() as cursor:
            return cursor.execute(sql, params)


def _case(case_id: str) -> dict:
    return CASE_BY_ID[case_id]


def _response_data(body: dict) -> dict:
    data = body.get("data")
    return data if isinstance(data, dict) else {}


def _login(client: ApiClient, account: str) -> str:
    response = client.request(
        "POST",
        "/v1/token",
        json={"account": account, "secret": "123456", "type": 100},
    )
    body = response.json()
    token = body.get("token") or _response_data(body).get("token")
    assert response.status_code == 200 and token, (
        f"测试账号 {account} 登录失败: {response.status_code} {response.text}"
    )
    return token


def _auth_client(base_url: str, timeout: int, token: str) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout, token=token)


def _post_order(client: ApiClient, case: dict, products: list[dict] | None = None):
    payload = {"products": products if products is not None else case.get("products", [])}
    payload.update(case.get("extra_json", {}))
    response = client.request("POST", "/v1/order", json=payload)
    attach_request_response({"case": case, "payload": payload}, response)
    return response, response.json(), payload


def _assert_created(response, body: dict) -> dict:
    data = _response_data(body)
    assert response.status_code == 200, response.text
    assert body.get("error_code") == 0, body
    assert data.get("pass") is True, body
    assert isinstance(data.get("order_id"), int) and data["order_id"] > 0, body
    assert data.get("order_no"), body
    return data


def _assert_rejected(response, body: dict) -> None:
    data = _response_data(body)
    rejected_by_http = response.status_code >= 400
    rejected_by_business = data.get("pass") is False or body.get("error_code", 0) != 0
    assert rejected_by_http or rejected_by_business, body


def _order_row(order_id: int) -> dict:
    row = _fetchone("SELECT * FROM `order` WHERE id=%s", (order_id,))
    assert row is not None, f"数据库中不存在订单 {order_id}"
    return row


def _relations(order_id: int) -> list[dict]:
    return _fetchall(
        "SELECT order_id, product_id, count FROM order_product WHERE order_id=%s ORDER BY product_id",
        (order_id,),
    )


def _product(product_id: int) -> dict:
    row = _fetchone("SELECT id, name, price, stock, main_img_url FROM product WHERE id=%s", (product_id,))
    assert row is not None
    return row


def _all_order_ids() -> set[int]:
    return {row["id"] for row in _fetchall("SELECT id FROM `order`")}


def _start_case(case: dict) -> None:
    allure.dynamic.title(f"{case['id']} - {case['summary']}")
    allure.dynamic.feature("成员三-订单业务")
    allure.dynamic.story(case["tag"])
    allure.dynamic.severity(
        allure.severity_level.CRITICAL if case.get("priority") == "P0" else allure.severity_level.NORMAL
    )


@pytest.fixture(scope="module", autouse=True)
def initialized_data():
    """执行前重建公共测试基线；模块结束时再恢复一次。"""
    command = [sys.executable, str(ROOT_DIR / "fake.py"), "--scope", "all"]
    subprocess.run(command, cwd=ROOT_DIR, check=True)
    yield
    subprocess.run(command, cwd=ROOT_DIR, check=True)


@pytest.fixture(scope="module")
def service_ready(base_url, initialized_data):
    """如果服务未运行则自动启动，并在模块结束后关闭本测试启动的进程。"""
    health_url = f"{base_url.rstrip('/')}/v1/product/1"
    process = None
    try:
        requests.get(health_url, timeout=1).raise_for_status()
    except requests.RequestException:
        process = subprocess.Popen(
            [sys.executable, str(ROOT_DIR / "server.py"), "run"],
            cwd=ROOT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(30):
            try:
                response = requests.get(health_url, timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.5)
        else:
            process.terminate()
            pytest.fail("自动启动Flask服务失败，30次健康检查均未通过")
    yield
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


@pytest.fixture(scope="module")
def client(base_url, timeout, service_ready) -> ApiClient:
    response = ApiClient(base_url=base_url, timeout=timeout).request("GET", "/v1/product/1")
    assert response.status_code == 200, "Flask服务不可用或商品基线不存在"
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> dict[str, str]:
    return {
        "user": _login(client, "user"),
        "Allen7D": _login(client, "Allen7D"),
    }


@pytest.fixture(autouse=True)
def isolate_case(initialized_data):
    """每条测试后删除新订单，并恢复商品1~3和地址2。"""
    before_ids = _all_order_ids()
    products_before = _fetchall(
        "SELECT id, name, price, stock, main_img_url FROM product WHERE id IN (1,2,3) ORDER BY id"
    )
    address_before = _fetchone("SELECT * FROM address WHERE id=2")
    yield
    new_ids = _all_order_ids() - before_ids
    if new_ids:
        placeholders = ",".join(["%s"] * len(new_ids))
        values = tuple(sorted(new_ids))
        _execute(f"DELETE FROM order_product WHERE order_id IN ({placeholders})", values)
        _execute(f"DELETE FROM `order` WHERE id IN ({placeholders})", values)
    for row in products_before:
        _execute(
            "UPDATE product SET name=%s, price=%s, stock=%s, main_img_url=%s WHERE id=%s",
            (row["name"], row["price"], row["stock"], row["main_img_url"], row["id"]),
        )
    if address_before:
        _execute(
            "UPDATE address SET name=%s,mobile=%s,province=%s,city=%s,country=%s,detail=%s,user_id=%s WHERE id=%s",
            (
                address_before["name"], address_before["mobile"], address_before["province"],
                address_before["city"], address_before["country"], address_before["detail"],
                address_before["user_id"], address_before["id"],
            ),
        )


@pytest.mark.order_business
def test_stock_sufficient_single_product(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-001")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    assert row["user_id"] == 31
    assert row["order_status"] == 1
    assert row["total_count"] == case["expected"]["total_count"]
    assert row["total_price"] == Decimal(str(case["expected"]["total_price"]))
    assert len(_relations(data["order_id"])) == 1


@pytest.mark.order_business
def test_stock_equal_boundary(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-002")
    _start_case(case)
    product = _product(case["product_id"])
    products = [{"product_id": product["id"], "count": product["stock"]}]
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case, products)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    assert row["total_count"] == product["stock"]
    items = json.loads(row["snap_items"])
    assert items[0]["has_stock"] is True


@pytest.mark.order_business
def test_stock_plus_one_rejected(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-003")
    _start_case(case)
    product = _product(case["product_id"])
    products = [{"product_id": product["id"], "count": product["stock"] + 1}]
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case, products)
    _assert_rejected(response, body)
    assert _response_data(body).get("order_id") == -1
    assert _all_order_ids() == before


@pytest.mark.order_business
def test_zero_stock_rejected(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-004")
    _start_case(case)
    _execute("UPDATE product SET stock=0 WHERE id=%s", (case["product_id"],))
    products = [{"product_id": case["product_id"], "count": case["count"]}]
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case, products)
    _assert_rejected(response, body)
    assert _response_data(body).get("order_id") == -1
    assert _all_order_ids() == before


@pytest.mark.order_business
def test_missing_product_rejected(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-005")
    _start_case(case)
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    _assert_rejected(response, body)
    assert _all_order_ids() == before


@pytest.mark.order_business
def test_multiple_products_success(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-006")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    assert row["total_count"] == 5
    assert row["total_price"] == Decimal("0.05")
    assert len(_relations(data["order_id"])) == 2


@pytest.mark.order_business
def test_one_insufficient_product_rejects_whole_order(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-007")
    _start_case(case)
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    _assert_rejected(response, body)
    assert _response_data(body).get("order_id") == -1
    assert _all_order_ids() == before


@pytest.mark.order_business
def test_duplicate_product_cannot_bypass_stock(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-008")
    _start_case(case)
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    _assert_rejected(response, body)
    assert response.status_code in case["expected"]["status_codes"], (
        f"重复商品应返回参数类错误，实际 {response.status_code}: {response.text}"
    )
    assert _all_order_ids() == before, "重复商品被分别校验，合计数量超过库存仍创建了订单"


@pytest.mark.order_business
def test_user_without_address_cannot_order(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-009")
    _start_case(case)
    assert _fetchone("SELECT id FROM address WHERE user_id=3") is None
    before = _all_order_ids()
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["Allen7D"]), case)
    _assert_rejected(response, body)
    assert _all_order_ids() == before


@pytest.mark.order_business
def test_single_product_amount(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-010")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    assert row["total_count"] == 10
    assert row["total_price"] == Decimal("0.10")


@pytest.mark.order_business
def test_multiple_product_amount(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-011")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    assert row["total_count"] == 60
    assert row["total_price"] == Decimal("0.60")


@pytest.mark.order_business
def test_client_amount_tampering_ignored(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-012")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    assert _order_row(data["order_id"])["total_price"] == Decimal("0.10")


@pytest.mark.order_business
def test_total_count_is_sum(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-013")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    assert _order_row(data["order_id"])["total_count"] == 9


@pytest.mark.order_business
def test_product_snapshot_complete(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-014")
    _start_case(case)
    product = _product(1)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    row = _order_row(data["order_id"])
    items = json.loads(row["snap_items"])
    assert set(case["expected"]["snapshot_fields"]).issubset(items[0])
    assert items[0]["name"] == product["name"]
    assert items[0]["count"] == 2
    assert row["snap_name"] == product["name"]
    assert row["snap_img"]


@pytest.mark.order_business
def test_product_snapshot_immutable(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-015")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    before = _order_row(data["order_id"])
    _execute("UPDATE product SET name=%s,price=%s,main_img_url=%s WHERE id=1", ("修改后商品", 99.99, "/changed.png"))
    after = _order_row(data["order_id"])
    for field in ("snap_name", "snap_img", "snap_items", "total_price"):
        assert after[field] == before[field]


@pytest.mark.order_business
def test_address_snapshot_immutable(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-016")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    before = _order_row(data["order_id"])["snap_address"]
    _execute("UPDATE address SET name=%s,detail=%s WHERE id=2", ("修改后收件人", "修改后地址"))
    after = _order_row(data["order_id"])["snap_address"]
    assert after == before


@pytest.mark.order_business
def test_order_product_relations_consistent(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-017")
    _start_case(case)
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    data = _assert_created(response, body)
    actual = {str(row["product_id"]): row["count"] for row in _relations(data["order_id"])}
    expected = {str(key): value for key, value in case["expected"]["relations"].items()}
    assert actual == expected


@pytest.mark.order_business
def test_failed_order_has_no_residue(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-018")
    _start_case(case)
    orders_before = _fetchone("SELECT COUNT(*) AS total FROM `order`")["total"]
    relations_before = _fetchone("SELECT COUNT(*) AS total FROM order_product")["total"]
    response, body, _ = _post_order(_auth_client(base_url, timeout, tokens["user"]), case)
    _assert_rejected(response, body)
    assert _fetchone("SELECT COUNT(*) AS total FROM `order`")["total"] == orders_before
    assert _fetchone("SELECT COUNT(*) AS total FROM order_product")["total"] == relations_before


@pytest.mark.order_business
def test_order_list_isolated_by_user(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-019")
    _start_case(case)
    auth_client = _auth_client(base_url, timeout, tokens["user"])
    create_case = _case("TC-M3-ORDER-001")
    response, body, _ = _post_order(auth_client, create_case)
    _assert_created(response, body)
    list_response = auth_client.request("GET", "/v1/order", params={"page": 1, "size": 100})
    attach_request_response({"case": case}, list_response)
    list_body = list_response.json()
    assert list_response.status_code == 200
    items = _response_data(list_body).get("items", [])
    assert items
    assert all(item.get("user_id") == 31 for item in items)


@pytest.mark.order_business
def test_order_detail_enforces_ownership(client, tokens, base_url, timeout):
    case = _case("TC-M3-ORDER-020")
    _start_case(case)
    row = _order_row(case["other_user_order_id"])
    assert row["user_id"] != 31
    response = _auth_client(base_url, timeout, tokens["user"]).request(
        "GET", f"/v1/order/{case['other_user_order_id']}"
    )
    attach_request_response({"case": case}, response)
    assert response.status_code in case["expected"]["status_codes"], (
        f"用户31读取了用户{row['user_id']}的订单: {response.status_code} {response.text}"
    )
