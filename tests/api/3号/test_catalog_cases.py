from pathlib import Path

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from support import fetchall, fetchone

CASES = CaseLoader(Path(__file__).resolve().parents[2]).load("cases/3号/catalog_cases.yaml")
C = {x["id"]: x for x in CASES}


def req(base_url, timeout, case, token=None):
    allure.dynamic.title(f"{case['id']} - {case['summary']}")
    return ApiClient(base_url, timeout, token).request(case["method"], case["path"], params=case.get("params"))


@pytest.mark.catalog_business
def test_category_all_matches_database(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-001"]); data = r.json()["data"]
    assert r.status_code == 200 and len(data) == fetchone("SELECT COUNT(*) n FROM category")["n"]
    assert {x["id"] for x in data} == {x["id"] for x in fetchall("SELECT id FROM category")}


@pytest.mark.catalog_business
def test_category_pagination(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-002"]); data = r.json()["data"]
    assert r.status_code == 200 and data["current_page"] == 1 and len(data["items"]) == 3 and data["total"] == 6


@pytest.mark.catalog_business
def test_category_detail_consistent(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-003"]); data = r.json()["data"]
    row = fetchone("SELECT id,name FROM category WHERE id=2")
    assert r.status_code == 200 and data["id"] == row["id"] and data["name"] == row["name"]


@pytest.mark.catalog_business
def test_category_missing(base_url, timeout, m3_environment):
    assert req(base_url, timeout, C["TC-M3-CATALOG-004"]).status_code == 404


@pytest.mark.catalog_business
def test_category_images_complete(base_url, timeout, m3_environment):
    data = req(base_url, timeout, C["TC-M3-CATALOG-005"]).json()["data"]
    assert data and all(x.get("image") for x in data)


@pytest.mark.catalog_business
def test_products_belong_to_requested_category(base_url, timeout, m3_environment):
    case = C["TC-M3-CATALOG-006"]; r = req(base_url, timeout, case); items = r.json()["data"]["items"]
    expected = {x["id"] for x in fetchall("SELECT id FROM product WHERE category_id=2")}
    assert r.status_code == 200 and {x["id"] for x in items} == expected


@pytest.mark.catalog_business
def test_theme_collection(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-007"]); items = r.json()["data"]["items"]
    assert r.status_code == 200 and {x["id"] for x in items} == {1, 2}


@pytest.mark.catalog_business
def test_theme_invalid_ids(base_url, timeout, m3_environment):
    assert req(base_url, timeout, C["TC-M3-CATALOG-008"]).status_code == 400


@pytest.mark.catalog_business
def test_theme_products_match_relation(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-009"]); products = r.json()["data"]["products"]
    expected = {x["product_id"] for x in fetchall("SELECT product_id FROM theme_product WHERE theme_id=1")}
    assert r.status_code == 200 and {x["id"] for x in products} == expected


@pytest.mark.catalog_business
def test_theme_list_requires_login(base_url, timeout, m3_environment):
    assert req(base_url, timeout, C["TC-M3-CATALOG-010"]).status_code == 401


@pytest.mark.catalog_business
def test_banner_items_complete(base_url, timeout, m3_environment):
    r = req(base_url, timeout, C["TC-M3-CATALOG-011"]); data = r.json()["data"]
    assert r.status_code == 200 and len(data["items"]) == 4
    assert all(x.get("image") and x.get("type") in (0, 1, 2) for x in data["items"])


@pytest.mark.catalog_business
def test_banner_missing(base_url, timeout, m3_environment):
    assert req(base_url, timeout, C["TC-M3-CATALOG-012"]).status_code == 404
