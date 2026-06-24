"""
系统测试 — 稳定性与兼容性测试（4号）

测试场景：
  S-14 : 持续30分钟请求（可通过 --duration 参数或 slow 标记控制时长）
  S-15 : 多角色访问验证（4种角色 × 11个端点）

运行方式：
  pytest tests/system/test_stability.py -v -m "stability and not slow"   # 短时（默认2分钟）
  pytest tests/system/test_stability.py -v -m slow                       # 完整30分钟
  pytest tests/system/test_stability.py -k S15 -v                        # 仅多角色
  pytest -m stability -v
"""

from __future__ import annotations

import os
import statistics
import time

import allure
import pytest
import requests

from tests.common.api_client import ApiClient
from tests.system.conftest import _fetchone

# ═══════════════════════════════════════════════════════════════════════════
# S-14: 持续请求稳定性测试
# ═══════════════════════════════════════════════════════════════════════════

# 默认测试时长（秒）：非 slow 模式用 120s，slow 模式用 1800s
DEFAULT_DURATION = 120  # 2 分钟
FULL_DURATION = 1800  # 30 分钟
SAMPLE_INTERVAL = 300  # 采样间隔（秒），普通模式改为60s


@pytest.mark.stability
def test_s14_continuous_requests_stability(base_url, timeout, tokens, request):
    """S-14: 持续请求，每5分钟采样内存/CPU/错误率

    时长控制:
      - 默认: 2 分钟 (用于快速验证)
      - 环境变量 STABILITY_DURATION=1800: 30 分钟完整测试
      - 命令行 -m slow: 30 分钟完整测试
    """
    # 根据命令行 -m slow 或环境变量 STABILITY_DURATION 决定时长
    markexpr = request.config.getoption("markexpr", default="")
    env_duration = os.environ.get("STABILITY_DURATION", "")
    # 精确匹配：只有当 "-m slow" 单独选中时才启用30分钟模式，避免 "not slow" 误匹配
    is_slow = markexpr.strip() == "slow" or env_duration == "1800"
    duration = FULL_DURATION if is_slow else DEFAULT_DURATION
    interval = SAMPLE_INTERVAL if is_slow else 60  # 短模式每60s采样

    allure.dynamic.title(
        f"持续请求稳定性 - S-14 (时长: {duration // 60}分钟)"
    )
    allure.dynamic.feature("系统测试-稳定性")
    allure.dynamic.story("持续运行")

    client = ApiClient(base_url, timeout, token=tokens["super"])
    auth_client = ApiClient(base_url, timeout, token=tokens["super"])

    # 统计累积器
    samples = []  # list of {elapsed_min, memory, cpu, total_req, success, fail, avg_latency}
    total_req = 0
    success_req = 0
    fail_req = 0
    all_latencies = []

    with allure.step(f"开始 {duration // 60} 分钟持续请求测试"):
        start_time = time.time()
        end_time = start_time + duration
        last_sample_time = start_time

        while time.time() < end_time:
            loop_start = time.time()

            # ---- 两个代表性请求 ----
            try:
                t1 = time.perf_counter()
                resp1 = client.request("GET", "/v1/product/1")
                lat1 = (time.perf_counter() - t1) * 1000
                total_req += 1
                if resp1.status_code == 200:
                    success_req += 1
                else:
                    fail_req += 1
                all_latencies.append(lat1)
            except Exception:
                fail_req += 1
                total_req += 1

            try:
                t2 = time.perf_counter()
                resp2 = auth_client.request(
                    "POST", "/v1/token",
                    json={"account": "super", "secret": "123456", "type": 100},
                )
                lat2 = (time.perf_counter() - t2) * 1000
                total_req += 1
                if resp2.status_code == 200:
                    success_req += 1
                else:
                    fail_req += 1
                all_latencies.append(lat2)
            except Exception:
                fail_req += 1
                total_req += 1

            # ---- 采样 ----
            now = time.time()
            if now - last_sample_time >= interval:
                elapsed_min = (now - start_time) / 60.0
                sample = _take_sample(base_url, timeout, tokens, elapsed_min, total_req, success_req, fail_req, all_latencies)
                samples.append(sample)
                last_sample_time = now

            # 控制请求频率（约每秒2次，避免打满）
            elapsed_loop = time.time() - loop_start
            if elapsed_loop < 0.5:
                time.sleep(0.5 - elapsed_loop)

    # ---- 最终采样 ----
    elapsed_min = (time.time() - start_time) / 60.0
    final_sample = _take_sample(base_url, timeout, tokens, elapsed_min, total_req, success_req, fail_req, all_latencies)
    if not samples or samples[-1]["elapsed_min"] != final_sample["elapsed_min"]:
        samples.append(final_sample)

    # ---- 生成报告 ----
    _attach_stability_report(samples, total_req, success_req, fail_req, all_latencies)

    # ---- 断言 ----
    with allure.step("校验稳定性指标"):
        success_rate = success_req / total_req if total_req > 0 else 0
        allure.attach(
            f"总请求: {total_req}, 成功: {success_req}, 失败: {fail_req}, 成功率: {success_rate:.2%}",
            name="最终统计",
            attachment_type=allure.attachment_type.TEXT,
        )
        assert success_rate >= 0.99, f"成功率过低: {success_rate:.2%}"

        # 检查内存趋势
        if len(samples) >= 2:
            first_mem_str = samples[0]["memory_percent"]
            last_mem_str = samples[-1]["memory_percent"]
            if first_mem_str != "N/A" and last_mem_str != "N/A":
                first_mem = float(first_mem_str.rstrip("%"))
                last_mem = float(last_mem_str.rstrip("%"))
                mem_growth = last_mem - first_mem
                allure.attach(
                    f"内存变化: {first_mem}% → {last_mem}% (增长 {mem_growth} 百分点)",
                    name="内存趋势",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 不硬断言（内存受系统影响大），但记录
                if mem_growth > 20:
                    allure.attach(
                        f"⚠️ 内存增长超过20个百分点，可能存在内存泄漏",
                        name="内存警告",
                        attachment_type=allure.attachment_type.TEXT,
                    )
            else:
                allure.attach(
                    "内存数据不可用 (N/A)，跳过内存趋势分析",
                    name="内存趋势",
                    attachment_type=allure.attachment_type.TEXT,
                )

        # 验证无500错误
        assert fail_req == 0, f"出现 {fail_req} 次失败请求"


def _take_sample(base_url, timeout, tokens, elapsed_min, total_req, success_req, fail_req, all_latencies):
    """采集一次系统状态样本"""
    client = ApiClient(base_url, timeout, token=tokens["super"])

    # 获取服务器状态（内存/CPU/磁盘一次性返回）
    memory_percent = "N/A"
    cpu_percent = "N/A"
    try:
        resp = client.request("GET", "/cms/server")
        if resp.status_code == 200:
            srv_data = resp.json().get("data", {})
            if isinstance(srv_data, dict):
                memory_percent = srv_data.get("memory", {}).get("percent", "N/A")
                cpu_percent = srv_data.get("cpu", {}).get("percent", "N/A")
    except Exception:
        pass

    avg_lat = statistics.mean(all_latencies) if all_latencies else 0

    return {
        "elapsed_min": round(elapsed_min, 1),
        "memory_percent": memory_percent,
        "cpu_percent": cpu_percent,
        "total_req": total_req,
        "success": success_req,
        "fail": fail_req,
        "avg_latency_ms": round(avg_lat, 2),
    }


def _attach_stability_report(samples, total_req, success_req, fail_req, all_latencies):
    """生成并附加稳定性报告到 Allure"""
    # 构建 Markdown 表格
    header = "| 时间(min) | 内存 | CPU | 累计请求 | 成功 | 失败 | 平均延迟(ms) |"
    sep = "|-----------|------|-----|---------|------|------|-------------|"
    rows = [
        f"| {s['elapsed_min']} | {s['memory_percent']} | {s['cpu_percent']} | "
        f"{s['total_req']} | {s['success']} | {s['fail']} | {s['avg_latency_ms']} |"
        for s in samples
    ]

    report = "\n".join([header, sep] + rows)
    success_rate = success_req / total_req if total_req > 0 else 0
    avg_all = statistics.mean(all_latencies) if all_latencies else 0
    p95 = (
        sorted(all_latencies)[int(len(all_latencies) * 0.95)]
        if all_latencies
        else 0
    )

    report += f"\n\n**总结**: 总请求={total_req}, 成功率={success_rate:.2%}, "
    report += f"平均延迟={avg_all:.2f}ms, P95={p95:.2f}ms"

    allure.attach(report, name="稳定性测试报告", attachment_type=allure.attachment_type.TEXT)


# ═══════════════════════════════════════════════════════════════════════════
# S-15: 多角色访问验证
# ═══════════════════════════════════════════════════════════════════════════

# 测试矩阵: (endpoint, method, super_expected, admin_expected, user_expected, anon_expected, note, extra_params)
ACCESS_MATRIX = [
    # ---- v1 公开接口 ----
    ("/v1/product/1", "GET", 200, 200, 200, 200, "公开商品详情", None),
    ("/v1/product/recent", "GET", 200, 200, 200, 200, "公开最近商品", None),
    # ---- v1 需登录接口 ----
    ("/v1/user", "GET", 200, 200, 200, 401, "需登录: 用户信息", None),
    ("/v1/order", "GET", 200, 200, 200, 401, "需登录: 订单列表", None),
    # ---- CMS 公开接口 ----
    ("/cms/menu", "GET", 200, 200, 200, 200, "公开: 菜单(需group_id参数)", {"group_id": 1}),
    ("/cms/server", "GET", 200, 200, 200, 200, "公开: 服务器状态", None),
    ("/cms/file/types", "GET", 200, 200, 200, 200, "公开: 文件类型", None),
    # ---- CMS admin_required ----
    ("/cms/admin/list", "GET", 200, 401, 401, 401, "admin_required: 管理员列表(需group_id)", {"group_id": 1}),
    ("/cms/group/all", "GET", 200, 401, 401, 401, "admin_required: 权限组列表", None),
    # ---- CMS group_required (auth=1 的普通用户也无法访问) ----
    ("/cms/log/oper/list/search", "GET", 200, 401, 401, 401, "group_required: 操作日志", None),
    # ---- 健康检查 ----
    ("/health", "GET", 200, 200, 200, 200, "健康检查(无鉴权)", None),
]

# 角色定义: (role_key, display_name)
ROLES = [
    ("super", "超级管理员"),
    ("admin", "管理员"),
    ("user", "普通用户"),
    ("anon", "未登录"),
]


@pytest.mark.stability
def test_s15_multi_role_access_verification(base_url, timeout, tokens):
    """S-15: 4种角色访问11个代表性端点，验证权限边界正确"""
    allure.dynamic.title("多角色访问验证 - S-15")
    allure.dynamic.feature("系统测试-稳定性")
    allure.dynamic.story("多角色兼容性")

    # 构建角色→ApiClient映射
    # 说明：admin 账号在数据库中可能不存在（取决于 fake.py 的种子数据），
    # 此时使用 user 的 token 作为替代（两者同属 auth=1 普通用户组）
    admin_token = tokens.get("admin") or tokens.get("user")
    clients = {
        "super": ApiClient(base_url, timeout, token=tokens["super"]),
        "admin": ApiClient(base_url, timeout, token=admin_token),
        "user": ApiClient(base_url, timeout, token=tokens["user"]),
        "anon": ApiClient(base_url, timeout),  # 无 token
    }

    results = []  # list of dict for report
    failures = []

    with allure.step("遍历 4角色 × 11端点 = 44个组合"):
        for endpoint, method, expected_super, expected_admin, expected_user, expected_anon, note, extra_params in ACCESS_MATRIX:
            expected_map = {
                "super": expected_super,
                "admin": expected_admin,
                "user": expected_user,
                "anon": expected_anon,
            }

            for role_key, role_name in ROLES:
                client = clients[role_key]
                expected = expected_map[role_key]

                # 对需要参数的特殊端点处理（优先使用矩阵中定义的 extra_params）
                path = endpoint
                params = extra_params

                try:
                    resp = client.request(method, path, params=params)
                    actual = resp.status_code
                except Exception as e:
                    actual = f"Exception: {e}"

                passed = actual == expected
                result = {
                    "endpoint": endpoint,
                    "method": method,
                    "role": role_name,
                    "expected": expected,
                    "actual": actual,
                    "passed": passed,
                    "note": note,
                }
                results.append(result)

                if not passed:
                    failures.append(result)

    # ---- 生成报告矩阵 ----
    with allure.step("生成权限矩阵报告"):
        report = _build_matrix_report(results)
        allure.attach(report, name="权限矩阵报告", attachment_type=allure.attachment_type.TEXT)

    # ---- 断言 ----
    with allure.step("校验所有权限边界"):
        if failures:
            fail_detail = "\n".join(
                f"  ❌ {f['role']} {f['method']} {f['endpoint']}: "
                f"期望 {f['expected']}, 实际 {f['actual']} ({f['note']})"
                for f in failures
            )
            allure.attach(fail_detail, name="失败详情", attachment_type=allure.attachment_type.TEXT)
            assert len(failures) == 0, (
                f"有 {len(failures)} 个权限边界不符合预期:\n{fail_detail}"
            )

    with allure.step("生成通过率汇总"):
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        allure.attach(
            f"通过: {passed}/{total} ({passed/total*100:.1f}%)",
            name="权限矩阵通过率",
            attachment_type=allure.attachment_type.TEXT,
        )


def _build_matrix_report(results):
    """构建格式化权限矩阵 Markdown 表格"""
    # 按端点分组
    endpoints = list(dict.fromkeys(r["endpoint"] for r in results))

    # 表头
    lines = ["## 多角色访问权限矩阵", ""]
    lines.append("| 端点 | 方法 | 超级管理员 | 管理员 | 普通用户 | 未登录 | 说明 |")
    lines.append("|------|------|:---:|:---:|:---:|:---:|------|")

    for ep in endpoints:
        ep_results = [r for r in results if r["endpoint"] == ep]
        if not ep_results:
            continue
        note = ep_results[0]["note"]
        method = ep_results[0]["method"]

        # 每个角色的结果
        role_status = {}
        for r in ep_results:
            icon = "✅" if r["passed"] else "❌"
            role_status[r["role"]] = f"{icon} {r['actual']}"

        lines.append(
            f"| {ep} | {method} | {role_status.get('超级管理员', '-')} | "
            f"{role_status.get('管理员', '-')} | {role_status.get('普通用户', '-')} | "
            f"{role_status.get('未登录', '-')} | {note} |"
        )

    # 总结
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    lines.append("")
    lines.append(f"**通过率**: {passed}/{total} ({passed/total*100:.1f}%)")

    return "\n".join(lines)
