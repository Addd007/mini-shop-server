from pathlib import Path

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.common.case_loader import CaseLoader
from support import execute, fetchone

CASES = CaseLoader(Path(__file__).resolve().parents[2]).load("cases/3号/order_state_cases.yaml")
C = {x["id"]: x for x in CASES}


def cms(base_url, timeout, token):
    return ApiClient(base_url, timeout, token)


def start(case):
    allure.dynamic.title(f"{case['id']} - {case['summary']}")


def set_status(order_id, status):
    execute("UPDATE `order` SET order_status=%s WHERE id=%s", (status, order_id))


@pytest.mark.order_state
def test_unpaid_cannot_deliver(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-001"]; start(case); set_status(1,1)
    r=cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":1})
    assert r.status_code == 403 and fetchone("SELECT order_status FROM `order` WHERE id=1")["order_status"] == 1


@pytest.mark.order_state
def test_paid_can_deliver(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-002"]; start(case); set_status(1,2)
    r=cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":1})
    assert r.status_code == 200, r.text
    assert fetchone("SELECT order_status FROM `order` WHERE id=1")["order_status"] == 3


@pytest.mark.order_state
def test_delivered_cannot_deliver_again(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-003"]; start(case); set_status(1,3)
    r=cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":1})
    assert r.status_code == 403 and fetchone("SELECT order_status FROM `order` WHERE id=1")["order_status"] == 3


@pytest.mark.order_state
def test_missing_order_cannot_deliver(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-004"]; start(case)
    r=cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":999999})
    assert r.status_code == 404


@pytest.mark.order_state
def test_invalid_order_id_rejected(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-005"]; start(case)
    r=cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":0})
    assert r.status_code == 400


@pytest.mark.order_state
def test_failed_transition_keeps_state(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-006"]; start(case); set_status(1,1)
    cms(base_url,timeout,m3_tokens["super"]).request("PUT","/cms/order/delivery",params={"order_id":1})
    assert fetchone("SELECT order_status FROM `order` WHERE id=1")["order_status"] == 1


@pytest.mark.order_state
def test_front_and_cms_state_consistent(base_url, timeout, m3_tokens):
    case=C["TC-M3-STATE-007"]; start(case); set_status(1,1)
    front=cms(base_url,timeout,m3_tokens["super"]).request("GET","/v1/order/1").json()["data"]
    back=cms(base_url,timeout,m3_tokens["super"]).request("GET","/cms/order/search",params={"order_no":case["order_no"]}).json()["data"]
    db=fetchone("SELECT order_status FROM `order` WHERE id=1")["order_status"]
    assert front["order_status"] == back["order_status"] == db
