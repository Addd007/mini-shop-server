"""
System Test A - Performance tests for member 3.

Covered scenarios:
  S-01: concurrent login requests against POST /v1/token
  S-02: concurrent product query requests against GET /v1/product/recent
  S-03: concurrent order creation and oversell protection against POST /v1/order

Run:
  pytest tests/system/test_performance.py -v -m perf
"""

from __future__ import annotations

import concurrent.futures
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable

import allure
import pytest

from tests.common.api_client import ApiClient
from tests.system.conftest import _execute, _fetchall, _fetchone


@dataclass
class RequestResult:
    ok: bool
    status_code: int | None
    latency_ms: float
    error: str = ""
    body: dict[str, Any] | None = None


def _percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * percent))))
    return ordered[index]


def _run_concurrently(
    worker: Callable[[int], RequestResult],
    *,
    total_requests: int,
    max_workers: int,
) -> tuple[list[RequestResult], float]:
    start = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        results = list(pool.map(worker, range(total_requests)))
    elapsed = time.perf_counter() - start
    return results, elapsed


def _metrics(results: list[RequestResult], elapsed_seconds: float) -> dict[str, Any]:
    latencies = [r.latency_ms for r in results if r.latency_ms >= 0]
    ok_count = sum(1 for r in results if r.ok)
    total = len(results)
    return {
        "total": total,
        "ok": ok_count,
        "failed": total - ok_count,
        "success_rate": ok_count / total if total else 0,
        "elapsed_seconds": round(elapsed_seconds, 3),
        "tps": round(total / elapsed_seconds, 2) if elapsed_seconds > 0 else 0,
        "avg_ms": round(statistics.mean(latencies), 2) if latencies else 0,
        "p50_ms": round(_percentile(latencies, 0.50), 2),
        "p95_ms": round(_percentile(latencies, 0.95), 2),
        "p99_ms": round(_percentile(latencies, 0.99), 2),
        "status_codes": {
            str(code): sum(1 for r in results if r.status_code == code)
            for code in sorted({r.status_code for r in results if r.status_code is not None})
        },
        "errors": [r.error for r in results if r.error][:10],
    }


def _attach_metrics(title: str, data: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"- total: {data['total']}",
        f"- ok: {data['ok']}",
        f"- failed: {data['failed']}",
        f"- success_rate: {data['success_rate']:.2%}",
        f"- elapsed_seconds: {data['elapsed_seconds']}",
        f"- TPS: {data['tps']}",
        f"- AVG(ms): {data['avg_ms']}",
        f"- P50(ms): {data['p50_ms']}",
        f"- P95(ms): {data['p95_ms']}",
        f"- P99(ms): {data['p99_ms']}",
        f"- status_codes: {data['status_codes']}",
    ]
    if data["errors"]:
        lines.append(f"- sample_errors: {data['errors']}")
    allure.attach("\n".join(lines), name=title, attachment_type=allure.attachment_type.TEXT)


def _json_or_empty(resp) -> dict[str, Any]:
    try:
        body = resp.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


@pytest.mark.perf
@pytest.mark.parametrize("concurrency", [50, 100, 200], ids=["S01_50", "S01_100", "S01_200"])
def test_s01_login_concurrent_pressure(base_url, timeout, ensure_running, concurrency):
    """S-01: login API concurrent pressure test."""
    allure.dynamic.title(f"S-01 Login concurrent pressure: {concurrency} requests")
    allure.dynamic.feature("System Test A - Performance")
    allure.dynamic.story("S-01 login concurrency")

    def worker(_: int) -> RequestResult:
        client = ApiClient(base_url, timeout)
        start = time.perf_counter()
        try:
            resp = client.request(
                "POST",
                "/v1/token",
                json={"account": "user", "secret": "123456", "type": 100},
            )
            latency = (time.perf_counter() - start) * 1000
            body = _json_or_empty(resp)
            token = body.get("token") or body.get("data", {}).get("token")
            return RequestResult(resp.status_code == 200 and bool(token), resp.status_code, latency, body=body)
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            return RequestResult(False, None, latency, error=f"{type(exc).__name__}: {exc}")

    results, elapsed = _run_concurrently(worker, total_requests=concurrency, max_workers=concurrency)
    data = _metrics(results, elapsed)
    _attach_metrics(f"S-01 login concurrency {concurrency}", data)

    min_success_rate = 0.90 if concurrency <= 100 else 0.80
    assert data["success_rate"] >= min_success_rate, (
        f"S-01 login success rate is too low: {data['success_rate']:.2%}, metrics={data}"
    )


@pytest.mark.perf
def test_s02_product_recent_concurrent_query(base_url, timeout, ensure_running):
    """S-02: product query concurrent pressure test."""
    allure.dynamic.title("S-02 Product query concurrent pressure: 200 requests")
    allure.dynamic.feature("System Test A - Performance")
    allure.dynamic.story("S-02 product query concurrency")

    concurrency = 200

    def worker(_: int) -> RequestResult:
        client = ApiClient(base_url, timeout)
        start = time.perf_counter()
        try:
            resp = client.request("GET", "/v1/product/recent", params={"count": 15})
            latency = (time.perf_counter() - start) * 1000
            body = _json_or_empty(resp)
            items = body.get("items") or body.get("data", {}).get("items")
            return RequestResult(resp.status_code == 200 and isinstance(items, list), resp.status_code, latency, body=body)
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            return RequestResult(False, None, latency, error=f"{type(exc).__name__}: {exc}")

    results, elapsed = _run_concurrently(worker, total_requests=concurrency, max_workers=concurrency)
    data = _metrics(results, elapsed)
    _attach_metrics("S-02 product recent concurrency 200", data)

    assert data["success_rate"] >= 0.90, (
        f"S-02 product query success rate is too low: {data['success_rate']:.2%}, metrics={data}"
    )


@pytest.mark.perf
def test_s03_concurrent_order_no_oversell(base_url, timeout, tokens):
    """S-03: concurrent order creation should not create more successful orders than stock."""
    allure.dynamic.title("S-03 Concurrent order and oversell protection")
    allure.dynamic.feature("System Test A - Performance")
    allure.dynamic.story("S-03 order concurrency / oversell")

    product_id = 1
    target_stock = 10
    request_count = 50
    user_token = tokens["user"]

    product_before = _fetchone("SELECT id, stock FROM product WHERE id=%s", (product_id,))
    assert product_before is not None, "baseline product 1 should exist"
    order_ids_before = {row["id"] for row in _fetchall("SELECT id FROM `order`")}

    _execute("UPDATE product SET stock=%s WHERE id=%s", (target_stock, product_id))

    def worker(_: int) -> RequestResult:
        client = ApiClient(base_url, timeout, token=user_token)
        start = time.perf_counter()
        try:
            resp = client.request(
                "POST",
                "/v1/order",
                json={"products": [{"product_id": product_id, "count": 1}]},
            )
            latency = (time.perf_counter() - start) * 1000
            body = _json_or_empty(resp)
            data = body.get("data", {}) if isinstance(body.get("data"), dict) else {}
            created = (
                resp.status_code in (200, 201)
                and body.get("error_code") in (0, 1)
                and isinstance(data.get("order_id"), int)
                and data.get("order_id") > 0
            )
            return RequestResult(created, resp.status_code, latency, body=body)
        except Exception as exc:
            latency = (time.perf_counter() - start) * 1000
            return RequestResult(False, None, latency, error=f"{type(exc).__name__}: {exc}")

    try:
        results, elapsed = _run_concurrently(worker, total_requests=request_count, max_workers=request_count)
        data = _metrics(results, elapsed)

        created_order_ids = []
        for result in results:
            body_data = result.body.get("data", {}) if result.body else {}
            oid = body_data.get("order_id")
            if result.ok and isinstance(oid, int):
                created_order_ids.append(oid)

        product_after = _fetchone("SELECT id, stock FROM product WHERE id=%s", (product_id,))
        new_order_ids = {row["id"] for row in _fetchall("SELECT id FROM `order`")} - order_ids_before
        order_product_total = _fetchone(
            "SELECT COALESCE(SUM(count), 0) AS total FROM order_product WHERE product_id=%s AND order_id IN ("
            + ",".join(["%s"] * len(new_order_ids))
            + ")",
            (product_id, *new_order_ids),
        )["total"] if new_order_ids else 0

        data.update(
            {
                "target_stock": target_stock,
                "created_order_ids": created_order_ids,
                "created_count": len(created_order_ids),
                "unique_created_order_ids": sorted(set(created_order_ids)),
                "unique_created_count": len(set(created_order_ids)),
                "db_new_order_count": len(new_order_ids),
                "db_order_product_total": int(order_product_total or 0),
                "stock_after": product_after["stock"] if product_after else None,
            }
        )
        _attach_metrics("S-03 concurrent order oversell", data)

        assert len(new_order_ids) <= target_stock, (
            f"S-03 oversell risk: DB created {len(new_order_ids)} orders with stock {target_stock}, metrics={data}"
        )
        assert int(order_product_total or 0) <= target_stock, (
            f"S-03 order_product total exceeds stock: {order_product_total} > {target_stock}, metrics={data}"
        )
        assert product_after is not None and product_after["stock"] >= 0, (
            f"S-03 stock should not become negative, metrics={data}"
        )
    finally:
        new_order_ids = {row["id"] for row in _fetchall("SELECT id FROM `order`")} - order_ids_before
        if new_order_ids:
            placeholders = ",".join(["%s"] * len(new_order_ids))
            values = tuple(sorted(new_order_ids))
            _execute(f"DELETE FROM order_product WHERE order_id IN ({placeholders})", values)
            _execute(f"DELETE FROM `order` WHERE id IN ({placeholders})", values)
        _execute("UPDATE product SET stock=%s WHERE id=%s", (product_before["stock"], product_id))
