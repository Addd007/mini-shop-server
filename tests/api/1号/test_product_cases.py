"""
商品接口自动化测试

测试依据：test_cases/1号/product.md
数据来源：tests/cases/1号/product_cases.yaml（YAML 数据驱动）
前置条件：服务已启动，且已执行 fake.py 初始化商品测试数据

测试分组：
  - product_recent        : 最近商品查询
  - product_detail        : 商品详情查询
  - product_list_category : 按分类查询商品列表
  - product_all_category  : 分类下所有商品
  - product_create        : 商品新增
  - product_update        : 商品更新
  - product_delete        : 商品删除
  - product_reorder       : 商品图片排序

运行方式：
  pytest tests/api/1号/test_product_cases.py -v
  pytest tests/api/1号/test_product_cases.py -k TC-PROD-001
  pytest -m product -v
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import subprocess
import sys

import allure
import pytest

from tests.common.allure_helper import attach_request_response
from tests.common.api_client import ApiClient
from tests.common.auth_seed import get_test_tokens
from tests.common.case_loader import CaseLoader


CASE_FILE = "cases/1号/product_cases.yaml"
MUTATING_TAGS = {"product_create", "product_update", "product_delete", "product_reorder"}


def _load_cases() -> list[dict[str, Any]]:
    loader = CaseLoader(Path(__file__).resolve().parents[2])
    return loader.load(CASE_FILE)


def _filter_by_tag(cases: list[dict], tag: str) -> list[dict]:
    return [case for case in cases if case.get("tag") == tag]


def _has_error(resp_json: dict) -> bool:
    error_code = resp_json.get("error_code", resp_json.get("code"))
    return error_code is not None and error_code != 0


def _skip_if_marked(case: dict) -> None:
    if case.get("skip"):
        pytest.skip(case.get("skip_reason", "用例已标记跳过"))


def _reset_test_data() -> None:
    subprocess.run(
        [sys.executable, str(Path(__file__).resolve().parents[3] / "fake.py"), "--scope", "products"],
        check=True,
    )


@pytest.fixture(scope="session", autouse=True)
def initialize_test_data():
    _reset_test_data()


@pytest.fixture(scope="module", autouse=True)
def isolate_mutating_product_cases():
    _reset_test_data()
    yield
    _reset_test_data()


ALL_CASES = _load_cases()
PRODUCT_RECENT_CASES = _filter_by_tag(ALL_CASES, "product_recent")
PRODUCT_DETAIL_CASES = _filter_by_tag(ALL_CASES, "product_detail")
PRODUCT_LIST_CATEGORY_CASES = _filter_by_tag(ALL_CASES, "product_list_category")
PRODUCT_ALL_CATEGORY_CASES = _filter_by_tag(ALL_CASES, "product_all_category")
PRODUCT_CREATE_CASES = _filter_by_tag(ALL_CASES, "product_create")
PRODUCT_UPDATE_CASES = _filter_by_tag(ALL_CASES, "product_update")
PRODUCT_DELETE_CASES = _filter_by_tag(ALL_CASES, "product_delete")
PRODUCT_REORDER_CASES = _filter_by_tag(ALL_CASES, "product_reorder")


@pytest.fixture(scope="module")
def client(base_url, timeout) -> ApiClient:
    return ApiClient(base_url=base_url, timeout=timeout)


@pytest.fixture(scope="module")
def tokens(client: ApiClient) -> Dict[str, str]:
    return get_test_tokens(client)


def _get_auth_client(client: ApiClient, tokens: Dict[str, str], auth: str) -> ApiClient:
    if auth == "none" or not auth:
        return ApiClient(base_url=client.base_url, timeout=client.timeout, token=None)
    return ApiClient(base_url=client.base_url, timeout=client.timeout, token=tokens.get(auth))


def _execute_case(client: ApiClient, tokens: Dict[str, str], case: dict) -> Any:
    auth_client = _get_auth_client(client, tokens, case.get("auth", "none"))
    return auth_client.request(
        method=case.get("method", "GET"),
        path=case.get("path", "/v1/product/recent"),
        json=case.get("json") if case.get("json") else None,
        params=case.get("params"),
        headers=case.get("headers"),
    )


def _attach_case(case: dict, resp: Any, request_payload: Any = None) -> None:
    payload = {"case": case, "request_payload": request_payload}
    attach_request_response(payload, resp)


def _assert_error_response(case: dict, resp, body: dict):
    if resp.status_code == 200 or resp.status_code == 201:
        assert _has_error(body), f"[{case['id']}] 业务应返回非零 error_code: {body}"
    else:
        assert resp.status_code in (400, 401, 403, 404, 422, 500), (
            f"[{case['id']}] 期望 4xx/5xx, 实际 {resp.status_code}"
        )


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_RECENT_CASES, ids=[c["id"] for c in PRODUCT_RECENT_CASES])
def test_product_recent(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"最近商品查询 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("最近商品查询")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_DETAIL_CASES, ids=[c["id"] for c in PRODUCT_DETAIL_CASES])
def test_product_detail(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"商品详情查询 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("商品详情查询")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_LIST_CATEGORY_CASES, ids=[c["id"] for c in PRODUCT_LIST_CATEGORY_CASES])
def test_product_list_by_category(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"按分类查询商品列表 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("按分类查询商品列表")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_ALL_CATEGORY_CASES, ids=[c["id"] for c in PRODUCT_ALL_CATEGORY_CASES])
def test_product_all_by_category(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"分类下所有商品 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("分类下所有商品")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_CREATE_CASES, ids=[c["id"] for c in PRODUCT_CREATE_CASES])
def test_product_create(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"商品新增 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("商品新增")
    _skip_if_marked(case)
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_UPDATE_CASES, ids=[c["id"] for c in PRODUCT_UPDATE_CASES])
def test_product_update(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"商品更新 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("商品更新")
    _skip_if_marked(case)
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_DELETE_CASES, ids=[c["id"] for c in PRODUCT_DELETE_CASES])
def test_product_delete(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"商品删除 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("商品删除")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)


@pytest.mark.product
@pytest.mark.parametrize("case", PRODUCT_REORDER_CASES, ids=[c["id"] for c in PRODUCT_REORDER_CASES])
def test_product_reorder(client: ApiClient, tokens: Dict[str, str], case: dict):
    allure.dynamic.title(f"商品图片排序 - {case['id']}")
    allure.dynamic.feature("商品管理")
    allure.dynamic.story("商品图片排序")
    resp = _execute_case(client, tokens, case)
    expected = case.get("expected", {})
    body = resp.json()
    _attach_case(case, resp, request_payload=case.get("json") or case.get("params"))
    if "status_code" in expected:
        with allure.step("校验 HTTP 状态码"):
            assert resp.status_code == expected["status_code"], (
                f"[{case['id']}] 期望 {expected['status_code']}, 实际 {resp.status_code}, body={resp.text}"
            )
    if expected.get("error"):
        with allure.step("校验错误响应"):
            _assert_error_response(case, resp, body)
