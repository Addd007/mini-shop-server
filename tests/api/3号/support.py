from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pymysql
import requests
from sqlalchemy.engine import make_url

from app.config.secure import SQLALCHEMY_DATABASE_URI
from tests.common.api_client import ApiClient

ROOT_DIR = Path(__file__).resolve().parents[3]
DB_URL = make_url(SQLALCHEMY_DATABASE_URI)


def db_connect():
    return pymysql.connect(host=DB_URL.host, port=DB_URL.port or 3306,
        user=DB_URL.username, password=DB_URL.password, database=DB_URL.database,
        charset="utf8mb4", cursorclass=pymysql.cursors.DictCursor, autocommit=True)


def fetchone(sql, params=()):
    with db_connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetchall(sql, params=()):
    with db_connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(sql, params=()):
    with db_connect() as conn, conn.cursor() as cur:
        return cur.execute(sql, params)


def reset_data():
    subprocess.run([sys.executable, str(ROOT_DIR / "fake.py"), "--scope", "all"],
                   cwd=ROOT_DIR, check=True)


def ensure_service(base_url: str):
    url = f"{base_url.rstrip('/')}/v1/product/1"
    process = None
    try:
        requests.get(url, timeout=1).raise_for_status()
    except requests.RequestException:
        process = subprocess.Popen([sys.executable, str(ROOT_DIR / "server.py"), "run"],
            cwd=ROOT_DIR, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(30):
            try:
                if requests.get(url, timeout=1).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.5)
        else:
            process.terminate()
            raise RuntimeError("Flask服务自动启动失败")
    return process


def stop_service(process):
    if process is not None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def login_token(base_url: str, timeout: int, account: str) -> str:
    client = ApiClient(base_url, timeout)
    resp = client.request("POST", "/v1/token",
        json={"account": account, "secret": "123456", "type": 100})
    body = resp.json()
    token = body.get("token") or (body.get("data") or {}).get("token")
    assert resp.status_code == 200 and token, f"{account}登录失败: {resp.text}"
    return token

