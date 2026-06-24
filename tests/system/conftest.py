"""
系统测试公共 fixture — 4号（恢复+部署+稳定性）+ 3号（性能+安全）共用

提供:
  - DB 直连辅助函数（pymysql）
  - 服务进程管理（启动/停止/强杀/等待就绪）
  - 预登录 token（super / admin / user / Allen3D）
  - 测试数据初始化（fake.py --scope all）
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, Optional

import psutil
import pymysql
import pytest
import requests
from sqlalchemy.engine import make_url

from tests.common.api_client import ApiClient
from tests.common.auth_seed import get_test_tokens

# ---------------------------------------------------------------------------
# 路径常量
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]
SERVER_SCRIPT = ROOT_DIR / "server.py"

# 直接解析 secure.py 获取 DB URI，避免触发完整 app import 链
_secure_path = ROOT_DIR / "app" / "config" / "secure.py"
_secure_ns = {}
with open(_secure_path, encoding="utf-8") as _f:
    exec(compile(_f.read(), str(_secure_path), "exec"), _secure_ns)
SQLALCHEMY_DATABASE_URI = _secure_ns["SQLALCHEMY_DATABASE_URI"]
DB_URL = make_url(SQLALCHEMY_DATABASE_URI)

# ---------------------------------------------------------------------------
# DB 直连辅助
# ---------------------------------------------------------------------------

def _db_connect() -> pymysql.connections.Connection:
    """创建 pymysql 连接（DictCursor, autocommit）"""
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


def _fetchone(sql: str, params=()) -> Optional[Dict[str, Any]]:
    with _db_connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _fetchall(sql: str, params=()) -> list:
    with _db_connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def _execute(sql: str, params=()) -> int:
    with _db_connect() as conn, conn.cursor() as cur:
        return cur.execute(sql, params)


# ---------------------------------------------------------------------------
# 服务进程管理
# ---------------------------------------------------------------------------

def _find_all_flask_pids() -> list[int]:
    """查找本项目的所有 Flask server.py 进程 PID"""
    target = str(SERVER_SCRIPT)  # 完整路径: C:\...\test\server.py
    pids = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            info = proc.info
            pname = (info["name"] or "").lower()
            if not pname.startswith("python"):
                continue
            cmdline = info.get("cmdline") or []
            for arg in cmdline:
                sarg = str(arg)
                if sarg == target or sarg.endswith("\\server.py"):
                    pids.append(info["pid"])
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return pids


def _find_flask_pid() -> Optional[int]:
    """查找第一个 Flask server.py 进程 PID"""
    pids = _find_all_flask_pids()
    return pids[0] if pids else None


def _find_pid_by_port(port: int = 5000) -> Optional[int]:
    """通过 netstat 查找占用指定端口的进程 PID（Windows 兼容）"""
    import subprocess as _sp
    try:
        result = _sp.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=10,
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid_str = parts[-1]
                if pid_str.isdigit():
                    return int(pid_str)
    except Exception:
        pass
    return None


def _kill_pid(pid: int) -> bool:
    """强制杀死指定 PID 的进程，返回是否成功"""
    try:
        p = psutil.Process(pid)
        p.kill()
        try:
            p.wait(timeout=5)
        except psutil.TimeoutExpired:
            pass
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _force_free_port(port: int = 5000, max_wait: int = 10) -> bool:
    """尽力确保端口空闲：先杀 Flask 进程，再杀端口占用者，轮询直到端口释放

    返回 True 表示端口已空闲，False 表示超时仍被占用。
    """
    # 第一轮：杀所有已知 Flask 进程
    _kill_all_flask()
    time.sleep(1)

    # 第二轮：杀端口占用者（可能不是 Flask，或 cmdline 匹配遗漏）
    deadline = time.time() + max_wait
    while time.time() < deadline:
        pid_on_port = _find_pid_by_port(port)
        if pid_on_port is None:
            # 端口空闲 — 再用 socket 双重确认
            if _is_port_free(port):
                return True
        else:
            _kill_pid(pid_on_port)
        time.sleep(0.5)

    return False


def _is_port_free(port: int = 5000) -> bool:
    """用 socket 尝试绑定端口，确认端口空闲"""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.bind(("127.0.0.1", port))
        s.close()
        return True
    except OSError:
        return False


def _kill_all_flask() -> int:
    """杀死所有本项目的 Flask 进程，返回杀死数量"""
    pids = _find_all_flask_pids()
    killed = 0
    for pid in pids:
        try:
            p = psutil.Process(pid)
            p.kill()
            try:
                p.wait(timeout=5)
            except psutil.TimeoutExpired:
                pass
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed


def _start_server(env_mode: Optional[str] = None) -> subprocess.Popen:
    """启动 Flask 服务，返回 Popen 对象"""
    env = os.environ.copy()
    if env_mode is not None:
        env["ENV_MODE"] = env_mode
    else:
        env.pop("ENV_MODE", None)  # 使用默认模式

    proc = subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT), "run"],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return proc


def _stop_server(proc: subprocess.Popen, timeout: int = 10):
    """优雅终止 Flask（SIGTERM）"""
    if proc is None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


def _kill_server(pid: int):
    """强制杀死进程（SIGKILL / Windows TerminateProcess）"""
    try:
        p = psutil.Process(pid)
        p.kill()  # SIGKILL on Unix, TerminateProcess on Windows
        p.wait(timeout=5)
    except psutil.NoSuchProcess:
        pass


def _wait_until_ready(base_url: str, timeout: int = 30) -> bool:
    """轮询直到服务就绪（/health 返回 200）"""
    url = f"{base_url.rstrip('/')}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    return False


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def initialize_module():
    """模块前后重置测试数据"""
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "fake.py"), "--scope", "all"],
        cwd=str(ROOT_DIR),
        check=True,
    )
    yield
    subprocess.run(
        [sys.executable, str(ROOT_DIR / "fake.py"), "--scope", "all"],
        cwd=str(ROOT_DIR),
        check=True,
    )


@pytest.fixture(scope="module")
def ensure_running(base_url: str):
    """确保 Flask 服务在测试期间运行（自动启动）"""
    # 检查是否已在运行
    if _wait_until_ready(base_url, timeout=3):
        yield
        return

    # 自动启动
    proc = _start_server()
    if not _wait_until_ready(base_url, timeout=30):
        _stop_server(proc)
        pytest.fail("Flask 服务自动启动失败")

    yield

    # 测试后保持运行（其他测试可能还需要）
    # 如需停止，由 server_process fixture 管理


@pytest.fixture(scope="module")
def server_process(base_url: str, ensure_running):
    """
    返回当前 Flask 进程的 PID，支持在测试中 kill/restart。
    依赖 ensure_running 确保初始时服务在运行。
    """
    pid = _find_flask_pid()
    if pid is None:
        pytest.fail("找不到 Flask 服务进程")
    return pid


@pytest.fixture(scope="module")
def tokens(base_url, timeout, initialize_module, ensure_running):
    """预登录三个核心角色，返回 {name: token}"""
    client = ApiClient(base_url, timeout)
    return get_test_tokens(
        client,
        accounts=(
            ("super", "super", "123456"),
            ("admin", "admin", "123456"),
            ("user", "user", "123456"),
        ),
    )


@pytest.fixture(scope="module")
def all_tokens(base_url, timeout, initialize_module, ensure_running):
    """预登录四个角色（含 Allen3D），返回 {name: token}"""
    client = ApiClient(base_url, timeout)
    return get_test_tokens(
        client,
        accounts=(
            ("super", "super", "123456"),
            ("admin", "admin", "123456"),
            ("user", "user", "123456"),
            ("Allen3D", "Allen3D", "123456"),
        ),
    )
