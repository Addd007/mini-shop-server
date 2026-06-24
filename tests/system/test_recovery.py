"""
系统测试 — 恢复测试（4号）

测试场景：
  S-09 : 服务kill后重启验证
  S-10 : 数据库断连恢复
  S-11 : 订单事务回滚验证

运行方式：
  pytest tests/system/test_recovery.py -v
  pytest tests/system/test_recovery.py -k S09
  pytest -m recovery -v
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import allure
import psutil
import pytest
import requests

from tests.common.api_client import ApiClient
from tests.system.conftest import (
    ROOT_DIR,
    _execute,
    _fetchall,
    _fetchone,
    _find_all_flask_pids,
    _find_flask_pid,
    _find_pid_by_port,
    _force_free_port,
    _kill_all_flask,
    _start_server,
    _stop_server,
    _wait_until_ready,
)

# ═══════════════════════════════════════════════════════════════════════════
# S-09: 服务 kill 后重启验证
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.recovery
def test_s09_service_kill_and_restart(base_url, timeout, tokens):
    """S-09: kill Flask 进程后重启，验证 Token 仍有效、数据完整"""
    allure.dynamic.title("服务kill后重启验证 - S-09")
    allure.dynamic.feature("系统测试-恢复")
    allure.dynamic.story("服务重启恢复")

    # ---- 1. 准备：确认服务正常 ----
    with allure.step("1. 确认服务正常运行"):
        client = ApiClient(base_url, timeout, token=tokens["super"])
        resp = client.request("GET", "/v1/product/1")
        assert resp.status_code == 200, f"服务异常: {resp.status_code}"
        product_before = resp.json()
        allure.attach(
            str(product_before),
            name="kill前 - product id=1 数据",
            attachment_type=allure.attachment_type.JSON,
        )

    # ---- 2. 获取一个有效 token 用于重启后验证 ----
    token_before = tokens["user"]

    # ---- 3. Kill 所有 Flask 进程并确保端口释放 ----
    with allure.step("2. Kill Flask 进程并确保端口释放"):
        pids_before = _find_all_flask_pids()
        assert len(pids_before) > 0, "找不到 Flask 进程"
        allure.attach(str(pids_before), name="目标进程PID列表", attachment_type=allure.attachment_type.TEXT)

        # 使用增强的端口释放：先杀 Flask 进程，再杀端口占用者（netstat），双重确认
        port_freed = _force_free_port(port=5000, max_wait=10)
        allure.attach(
            f"端口释放结果: {'成功' if port_freed else '失败'}",
            name="端口释放",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---- 4. 验证不可达 ----
    with allure.step("3. 验证服务不可达"):
        unreachable = False
        for attempt in range(5):
            try:
                requests.get(f"{base_url.rstrip('/')}/v1/product/1", timeout=2)
                if not port_freed:
                    # 端口仍被占用 — 但仍尝试验证
                    pass
                time.sleep(1)
            except requests.ConnectionError:
                unreachable = True
                break
            except requests.Timeout:
                unreachable = True
                break
        remaining = _find_all_flask_pids()
        port_pid = _find_pid_by_port(5000)
        assert unreachable, (
            f"kill 后服务应不可达（5次尝试均成功）。"
            f"剩余Flask进程: {remaining}, 端口占用PID: {port_pid}"
        )

    # ---- 5. 重启服务 ----
    with allure.step("4. 重启 Flask 服务"):
        proc = _start_server()
        ready = _wait_until_ready(base_url, timeout=30)
        assert ready, "服务重启失败（30s内未就绪）"

    # ---- 6. 验证恢复 ----
    with allure.step("5. 验证数据完整性"):
        client2 = ApiClient(base_url, timeout, token=tokens["super"])
        resp = client2.request("GET", "/v1/product/1")
        assert resp.status_code == 200, f"重启后接口异常: {resp.status_code}"
        product_after = resp.json()
        allure.attach(
            str(product_after),
            name="重启后 - product id=1 数据",
            attachment_type=allure.attachment_type.JSON,
        )
        assert product_before.get("id") == product_after.get("id"), "数据不一致"
        assert product_before.get("name") == product_after.get("name"), "数据不一致"

    with allure.step("6. 验证 Token 在重启后仍有效（stateless token）"):
        client3 = ApiClient(base_url, timeout, token=token_before)
        resp = client3.request("GET", "/v1/user")
        assert resp.status_code == 200, (
            f"重启后 token 应仍有效（stateless），实际: {resp.status_code}"
        )

    with allure.step("7. 验证 /health 恢复正常"):
        resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"

    # ---- 7. 验证订单状态不变 ----
    with allure.step("8. 验证订单数据完整"):
        orders = _fetchall("SELECT id, order_no, order_status FROM `order` LIMIT 5")
        allure.attach(
            str(orders),
            name="数据库中订单数据（前5条）",
            attachment_type=allure.attachment_type.JSON,
        )
        assert len(orders) > 0, "订单数据不应丢失"


# ═══════════════════════════════════════════════════════════════════════════
# S-10: 数据库断连恢复
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.recovery
def test_s10_database_disconnect_recovery(base_url, timeout, tokens):
    """S-10: 断开 MySQL 连接后验证 SQLAlchemy 自动重连"""
    allure.dynamic.title("数据库断连恢复 - S-10")
    allure.dynamic.feature("系统测试-恢复")
    allure.dynamic.story("数据库断连恢复")

    # ---- 方案 A: Kill MySQL 连接，验证自动重连 ----
    with allure.step("1. 正常请求基线"):
        client = ApiClient(base_url, timeout, token=tokens["super"])
        resp = client.request("GET", "/v1/product/recent")
        assert resp.status_code == 200, f"基线请求失败: {resp.status_code}"

    with allure.step("2. 查找并 Kill Flask→MySQL 的连接"):
        my_id = _fetchone("SELECT CONNECTION_ID()")["CONNECTION_ID()"]
        # 查询当前所有到 zerd 数据库的连接（包括 Sleep 状态的连接池连接）
        connections = _fetchall("SHOW PROCESSLIST")
        flask_conn_ids = [
            c["Id"]
            for c in connections
            if c.get("db") == "zerd"
            and c.get("Id") != my_id  # 不kill自己的连接
        ]

        if flask_conn_ids:
            for conn_id in flask_conn_ids[:10]:  # 最多杀10个
                try:
                    _execute(f"KILL CONNECTION {conn_id}")
                except Exception:
                    pass  # 忽略已断开的连接
            allure.attach(
                f"Killed connections: {flask_conn_ids[:10]} (共{len(flask_conn_ids)}个)",
                name="已终止的连接",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            allure.attach(
                "未找到 Flask 的 DB 连接",
                name="连接状态",
                attachment_type=allure.attachment_type.TEXT,
            )

    with allure.step("3. Kill 后请求 — SQLAlchemy 自动重连"):
        # 说明：SQLAlchemy 默认未启用 pool_pre_ping，连接池中每个被 kill 的
        # 连接在第一次被检出使用时会导致一个 500 错误（MySQL server has gone away），
        # 随后该无效连接被丢弃。因此前 N 个请求可能失败（N=连接池大小），
        # 之后自动创建新连接并恢复正常。
        time.sleep(0.5)  # 短暂等待
        results = []
        success_count = 0
        for i in range(10):
            try:
                resp = client.request("GET", "/v1/product/recent")
                results.append(f"Req {i+1}: {resp.status_code}")
                if resp.status_code == 200:
                    success_count += 1
            except Exception as e:
                results.append(f"Req {i+1}: {type(e).__name__}: {str(e)[:100]}")

        allure.attach(
            "\n".join(results),
            name="请求结果序列",
            attachment_type=allure.attachment_type.TEXT,
        )
        allure.attach(
            f"10次请求中 {success_count} 次成功",
            name="自动重连结果",
            attachment_type=allure.attachment_type.TEXT,
        )
        # 容许前几个请求因连接池中残留的无效连接而失败，但后续应恢复
        assert success_count >= 5, (
            f"DB连接被kill后应能自动重连，实际成功率: {success_count}/10\n"
            + "\n".join(results)
        )

    # ---- 方案 B: 手动断连说明（不自动执行） ----
    with allure.step("4. 手动断连测试说明"):
        allure.attach(
            "手动断连测试步骤:\n"
            "1. 在终端执行: net stop MySQL80\n"
            "2. 调用 GET /v1/product/1 → 预期返回 500\n"
            "3. 执行: net start MySQL80\n"
            "4. 等待 10-30s → 再次调用 GET /v1/product/1 → 预期 200\n"
            "5. 截图记录错误信息和恢复过程",
            name="手动断连测试步骤 (S-10B)",
            attachment_type=allure.attachment_type.TEXT,
        )


# ═══════════════════════════════════════════════════════════════════════════
# S-11: 订单事务回滚验证
# ═══════════════════════════════════════════════════════════════════════════


def _count_orders():
    return _fetchone("SELECT COUNT(*) as cnt FROM `order`")["cnt"]


def _count_order_products():
    return _fetchone("SELECT COUNT(*) as cnt FROM order_product")["cnt"]


@pytest.mark.recovery
@pytest.mark.parametrize(
    "scenario,payload,expected_status,desc",
    [
        # 商品不存在 → OrderException，事务回滚
        (
            "product_not_exist",
            {"products": [{"product_id": 99999, "count": 1}]},
            400,
            "商品不存在",
        ),
        # 库存不足 — 动态由测试函数内查找 stock=0 商品
        (
            "insufficient_stock",
            {"products": [{"product_id": -1, "count": 99999}]},  # -1 为占位，测试内动态替换
            400,
            "库存不足",
        ),
        # 缺少 products 字段 → 参数校验异常
        (
            "missing_products",
            {},
            400,
            "缺少products参数",
        ),
        # 正常下单（正向对照）
        (
            "normal_order",
            {"products": [{"product_id": 1, "count": 1}]},
            200,
            "正常下单(对照)",
        ),
    ],
    ids=["商品不存在", "库存不足", "缺少products", "正常下单(对照)"],
)
def test_s11_order_transaction_rollback(
    base_url, timeout, tokens, scenario, payload, expected_status, desc
):
    """S-11: 下单异常时验证事务回滚，order 和 order_product 表无脏数据"""
    allure.dynamic.title(f"订单事务回滚 - S-11 ({desc})")
    allure.dynamic.feature("系统测试-恢复")
    allure.dynamic.story("事务回滚")

    # ---- 0. 正常下单场景需要预置配送地址 ----
    if scenario == "normal_order":
        user_info = _fetchone(
            "SELECT id FROM user WHERE nickname = '普通用户'"
        )
        if user_info:
            uid = user_info["id"]
            existing = _fetchone(
                "SELECT id FROM address WHERE user_id = %s", (uid,)
            )
            if not existing:
                _execute(
                    "INSERT INTO address (user_id, name, mobile, province, city, country, detail) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (uid, "测试用户", "13700000003", "广东省", "广州市", "天河区", "测试路100号"),
                )

    # ---- 特殊处理：库存不足场景需要动态查找 stock=0 的商品 ----
    actual_payload = dict(payload)
    if scenario == "insufficient_stock":
        zero_stock_product = _fetchone(
            "SELECT id, stock FROM product WHERE stock = 0 ORDER BY id LIMIT 1"
        )
        if zero_stock_product is None:
            # 没有 stock=0 的商品，选一个存在的商品但设超大数量
            any_product = _fetchone("SELECT id, stock FROM product WHERE stock > 0 ORDER BY id LIMIT 1")
            actual_payload = {
                "products": [{"product_id": any_product["id"], "count": any_product["stock"] + 1000}]
            }
        else:
            actual_payload = {
                "products": [{"product_id": zero_stock_product["id"], "count": 100}]
            }

    # ---- 1. 记录基线 ----
    with allure.step("1. 记录基线"):
        baseline_orders = _count_orders()
        baseline_op = _count_order_products()
        allure.attach(
            f"baseline orders={baseline_orders}, order_products={baseline_op}",
            name="基线计数",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ---- 2. 执行下单 ----
    with allure.step(f"2. 执行下单: {desc}"):
        client = ApiClient(base_url, timeout, token=tokens["user"])
        resp = client.request("POST", "/v1/order", json=actual_payload)

    # ---- 3. 验证 ----
    with allure.step("3. 验证结果"):
        current_orders = _count_orders()
        current_op = _count_order_products()
        resp_data = resp.json().get("data", {}) if resp.status_code == 200 else {}

        if scenario == "normal_order":
            # 正常下单：order 和 order_product 应该各 +1
            assert resp.status_code == 200, (
                f"正常下单应返回200，实际: {resp.status_code}, body: {resp.text[:200]}"
            )
            assert current_orders == baseline_orders + 1, (
                f"正常下单后 order 表应 +1，基线={baseline_orders}，当前={current_orders}"
            )
            assert current_op == baseline_op + 1, (
                f"正常下单后 order_product 表应 +1，基线={baseline_op}，当前={current_op}"
            )
            allure.attach("正向对照通过：order+1, order_product+1", name="结果")
        elif scenario == "insufficient_stock":
            # 库存不足：API 返回 200 但 data.pass=false, data.order_id=-1
            # 这是预期的业务"软失败"—事务已回滚
            is_soft_fail = (
                resp.status_code == 200
                and resp_data.get("pass") == False
                and resp_data.get("order_id") == -1
            )
            assert is_soft_fail, (
                f"库存不足应返回 200 + pass=false，实际: status={resp.status_code}, body={resp.text[:200]}"
            )
            assert current_orders == baseline_orders, (
                f"[{desc}] 异常下单不应产生订单记录: 基线={baseline_orders}，当前={current_orders}"
            )
            assert current_op == baseline_op, (
                f"[{desc}] 异常下单不应产生 order_product 记录: 基线={baseline_op}，当前={current_op}"
            )
            allure.attach(
                f"事务回滚验证通过: pass=false, order_id=-1, "
                f"orders无变化 ({baseline_orders}→{current_orders}), "
                f"order_products无变化 ({baseline_op}→{current_op})",
                name="事务回滚结果",
                attachment_type=allure.attachment_type.TEXT,
            )
        else:
            # 商品不存在 / 缺少 products：应返回非200
            assert resp.status_code != 200, (
                f"异常场景应返回非200，实际: {resp.status_code}, body: {resp.text[:200]}"
            )
            assert current_orders == baseline_orders, (
                f"[{desc}] 异常下单不应产生订单记录: 基线={baseline_orders}，当前={current_orders}"
            )
            assert current_op == baseline_op, (
                f"[{desc}] 异常下单不应产生 order_product 记录: 基线={baseline_op}，当前={current_op}"
            )
            allure.attach(
                f"事务回滚验证通过: orders无变化 ({baseline_orders}→{current_orders}), "
                f"order_products无变化 ({baseline_op}→{current_op})",
                name="事务回滚结果",
                attachment_type=allure.attachment_type.TEXT,
            )

    # ---- 4. 清理（正常下单场景）----
    if scenario == "normal_order":
        with allure.step("4. 清理测试订单"):
            # 查找本次创建的最新的 order
            latest = _fetchone("SELECT id FROM `order` ORDER BY id DESC LIMIT 1")
            if latest:
                _execute("DELETE FROM order_product WHERE order_id = %s", (latest["id"],))
                _execute("DELETE FROM `order` WHERE id = %s", (latest["id"],))
