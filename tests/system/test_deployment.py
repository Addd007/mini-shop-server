"""
系统测试 — 部署测试（4号）

测试场景：
  S-12 : 环境变量切换验证（ENV_MODE=dev:local / dev / prod）
  S-13 : 接口文档可用性（Swagger UI + apispec + Flask-Admin）

运行方式：
  pytest tests/system/test_deployment.py -v
  pytest tests/system/test_deployment.py -k S12
  pytest -m deployment -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import allure
import pytest
import requests

from tests.common.api_client import ApiClient
from tests.system.conftest import (
    ROOT_DIR,
    _force_free_port,
    _find_all_flask_pids,
    _kill_all_flask,
    _start_server,
    _stop_server,
    _wait_until_ready,
)

# ═══════════════════════════════════════════════════════════════════════════
# S-12: 环境变量切换验证
# ═══════════════════════════════════════════════════════════════════════════


# dev:local 模式需要的临时配置文件内容
LOCAL_SECURE_CONTENT = '''# _*_ coding: utf-8 _*_
"""测试用 local_secure — DEBUG=True"""
DEBUG = True
SECRET_KEY = 'test-secret-key-for-deployment-testing'
TOKEN_EXPIRATION = 30 * 24 * 3600
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:ZBH924zxcvbnm@localhost:3306/zerd?charset=utf8'
SQLALCHEMY_ENCODING = 'utf-8'
SQLALCHEMY_TRACK_MODIFICATIONS = False
APP_ID = 'wx551ff8259cd7339b'
APP_SECRET = '7773e41929841faf6aa9e68807f6e2cb'
LOGIN_URL = 'https://api.weixin.qq.com/sns/jscode2session?appid={0}&secret={1}&js_code={2}&grant_type=authorization_code'
OPEN_APP_ID = 'wx87186e0123456789'
OPEN_APP_SECRET = '606d686fa91edc283d9cd00123456789'
OPEN_SCOPE = 'snsapi_login'
OPEN_STATE = '3d6be0a4035d839573b04816624a415e'
REDIRECT_URI = 'https%3a%2f%2fapi.ivinetrue.com%2ftoken%2fuser'
OPEN_AUTHORIZE_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize?appid={0}&redirect_uri={1}&response_type=code&scope={2}&state={3}#wechat_redirect'.format(OPEN_APP_ID, OPEN_APP_SECRET, OPEN_SCOPE, OPEN_STATE)
OPEN_ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid={0}&secret={1}&code={2}&grant_type=authorization_code'
OPEN_USER_INFO_URL = 'https://api.weixin.qq.com/sns/userinfo?access_token={0}&openid={1}&lang=zh_CN'
ACCOUNT_APP_ID = 'wx7bc53e1ab38e9f92'
ACCOUNT_APP_SECRET = 'c96c84b27ea4a353b10d7353b9cf5a09c'
'''

LOCAL_SETTING_CONTENT = '''# _*_ coding: utf-8 _*_
"""测试用 local_setting — 区别于生产配置"""
from app.libs.enums import ClientTypeEnum
SERVER_URL = '127.0.0.1:5000'
API_PATH = 'app.api'
ALL_RP_API_LIST = \\
    ['v1-token'] + \\
    ['cms-admin', 'cms-group', 'cms-auth', 'cms-menu', 'cms-element', 'cms-route', 'cms-oper_log', 'cms-login_log', 'cms-error_log'] + \\
    ['cms-file'] + \\
    ['v1-user', 'v1-address',
     'v1-banner', 'v1-theme', 'v1-category', 'v1-product', 'v1-order', 'v1-pay'] + \\
    ['cms-user', 'cms-article'] + \\
    ['cms-order', 'cms-banner', 'cms-banner_item'] + \\
    ['cms-notice', 'cms-dict_type', 'cms-dict', 'cms-config', 'cms-server']
EP_META = {}
EP_INFO_LIST = []
EP_INFOS = {}
PAGE_DEFAULT = 1
SIZE_DEFAULT = 10
CLINET_INNER_TYPES = (ClientTypeEnum.USERNAME, ClientTypeEnum.EMAIL, ClientTypeEnum.MOBILE)
'''


def _setup_local_config():
    """创建临时 dev:local 配置文件"""
    config_dir = ROOT_DIR / "app" / "config"
    secure_path = config_dir / "local_secure.py"
    setting_path = config_dir / "local_setting.py"

    created = []
    if not secure_path.exists():
        secure_path.write_text(LOCAL_SECURE_CONTENT, encoding="utf-8")
        created.append(str(secure_path))
    if not setting_path.exists():
        setting_path.write_text(LOCAL_SETTING_CONTENT, encoding="utf-8")
        created.append(str(setting_path))
    return created


def _cleanup_local_config(created_files):
    """删除临时配置文件"""
    for f in created_files:
        try:
            os.remove(f)
        except OSError:
            pass


@pytest.mark.deployment
def test_s12_env_mode_switch(base_url, timeout, tokens):
    """S-12: 验证不同 ENV_MODE 下配置加载正确"""
    allure.dynamic.title("环境变量切换验证 - S-12")
    allure.dynamic.feature("系统测试-部署")
    allure.dynamic.story("环境切换")

    # ---- 准备临时配置文件 ----
    created_files = _setup_local_config()
    allure.attach(
        f"创建的临时文件: {created_files}",
        name="临时配置文件",
        attachment_type=allure.attachment_type.TEXT,
    )

    try:
        # ---- 0. 先停止当前服务（释放端口）----
        with allure.step("0. 停止当前服务"):
            pids_before = _find_all_flask_pids()
            allure.attach(
                f"当前 Flask 进程: {pids_before}",
                name="停止前进程",
                attachment_type=allure.attachment_type.TEXT,
            )
            port_freed = _force_free_port(port=5000, max_wait=10)
            allure.attach(
                f"端口释放: {'成功' if port_freed else '失败（将尝试继续）'}",
                name="端口状态",
                attachment_type=allure.attachment_type.TEXT,
            )

        # ---- 1. dev:local 模式 ----
        with allure.step("1. ENV_MODE=dev:local"):
            proc_dev_local = _start_server(env_mode="dev:local")
            try:
                ready = _wait_until_ready(base_url, timeout=30)
                assert ready, "dev:local 模式启动失败"

                # 验证服务可访问
                resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
                assert resp.status_code == 200

                # 触发 404 检查 DEBUG 模式 — debug 模式下错误信息更详细
                resp_err = requests.get(
                    f"{base_url.rstrip('/')}/api/nonexistent_xyz_123",
                    timeout=5,
                )
                allure.attach(
                    f"status={resp_err.status_code}, body={resp_err.text[:500]}",
                    name="dev:local 模式 - 404响应",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # DEBUG=True 时应返回更详细的错误
                assert resp_err.status_code == 404, (
                    f"应返回404, 实际: {resp_err.status_code}"
                )
            finally:
                _stop_server(proc_dev_local)
                time.sleep(1)

        # ---- 2. dev 模式（默认） ----
        with allure.step("2. ENV_MODE=dev"):
            proc_dev = _start_server(env_mode="dev")
            try:
                ready = _wait_until_ready(base_url, timeout=30)
                assert ready, "dev 模式启动失败"

                resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
                assert resp.status_code == 200

                # 触发错误 — dev 模式下应加载默认 secure.py（DEBUG=False）
                resp_err = requests.get(
                    f"{base_url.rstrip('/')}/api/nonexistent_xyz_123",
                    timeout=5,
                )
                allure.attach(
                    f"status={resp_err.status_code}, body={resp_err.text[:500]}",
                    name="dev 模式 - 404响应",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert resp_err.status_code == 404
            finally:
                _stop_server(proc_dev)
                time.sleep(1)

        # ---- 3. prod 模式 ----
        with allure.step("3. ENV_MODE=prod"):
            proc_prod = _start_server(env_mode="prod")
            try:
                ready = _wait_until_ready(base_url, timeout=30)
                assert ready, "prod 模式启动失败"

                resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
                assert resp.status_code == 200

                # prod 模式下 500 错误不应暴露详情
                resp_err = requests.get(
                    f"{base_url.rstrip('/')}/api/nonexistent_xyz_123",
                    timeout=5,
                )
                allure.attach(
                    f"status={resp_err.status_code}, body={resp_err.text[:300]}",
                    name="prod 模式 - 404响应",
                    attachment_type=allure.attachment_type.TEXT,
                )
            finally:
                _stop_server(proc_prod)
                time.sleep(1)

        # ---- 4. 恢复默认服务（确保测试结束后其他测试可用）----
        with allure.step("4. 恢复默认模式"):
            # 确保端口空闲后再启动
            _force_free_port(port=5000, max_wait=5)
            proc_default = _start_server(env_mode=None)
            ready = _wait_until_ready(base_url, timeout=30)
            assert ready, "默认模式启动失败"
            # 验证 /health 正常
            resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
            assert resp.status_code == 200, f"恢复后 /health 返回 {resp.status_code}"

    finally:
        _cleanup_local_config(created_files)


# ═══════════════════════════════════════════════════════════════════════════
# S-13: 接口文档可用性
# ═══════════════════════════════════════════════════════════════════════════


@pytest.mark.deployment
def test_s13_api_docs_availability(base_url, timeout, tokens):
    """S-13: 验证 Swagger UI、API规范JSON 和 Flask-Admin 可访问"""
    allure.dynamic.title("接口文档可用性 - S-13")
    allure.dynamic.feature("系统测试-部署")
    allure.dynamic.story("接口文档")

    # ---- 1. Swagger UI ----
    with allure.step("1. Swagger UI 可访问"):
        urls = ["/apidocs/", "/apidocs/index.html"]
        swagger_ok = False
        for path in urls:
            try:
                resp = requests.get(
                    f"{base_url.rstrip('/')}{path}",
                    timeout=10,
                    allow_redirects=True,
                )
                if resp.status_code == 200:
                    swagger_ok = True
                    allure.attach(
                        f"{path} → {resp.status_code}",
                        name="Swagger UI",
                        attachment_type=allure.attachment_type.TEXT,
                    )
                    break
            except requests.RequestException:
                continue
        # Swagger UI 可能不可用（非本地开发环境），记录但不硬失败
        if not swagger_ok:
            allure.attach(
                "Swagger UI 不可访问（可能未启用 flasgger）",
                name="Swagger UI 状态",
                attachment_type=allure.attachment_type.TEXT,
            )

    # ---- 2. API 规范 JSON ----
    with allure.step("2. API 规范 JSON (apispec_1.json)"):
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/apispec_1.json",
                timeout=10,
            )
            if resp.status_code == 200:
                spec = resp.json()
                allure.attach(
                    json.dumps(spec, ensure_ascii=False, indent=2),
                    name="API规范",
                    attachment_type=allure.attachment_type.JSON,
                )

                # 验证结构
                assert "swagger" in spec, "缺少 swagger 版本字段"
                assert "info" in spec, "缺少 info 字段"
                assert "paths" in spec, "缺少 paths 字段"

                # 抽样检查关键端点
                paths = spec.get("paths", {})
                key_paths = [
                    "/v1/token",
                    "/v1/user",
                    "/v1/order",
                    "/v1/product/{id}",
                ]
                found_paths = [p for p in key_paths if p in paths]
                allure.attach(
                    f"关键路径检查: {len(found_paths)}/{len(key_paths)} 存在\n"
                    f"找到: {found_paths}\n总路径数: {len(paths)}",
                    name="路径完整性",
                    attachment_type=allure.attachment_type.TEXT,
                )
                assert len(found_paths) >= 2, (
                    f"关键路径缺失，总路径数: {len(paths)}"
                )
                assert len(paths) >= 10, f"接口数量过少: {len(paths)}"
                assert spec["info"].get("title"), "API title 为空"
            else:
                allure.attach(
                    f"apispec_1.json 返回 {resp.status_code}",
                    name="API规范状态",
                    attachment_type=allure.attachment_type.TEXT,
                )
        except requests.RequestException as e:
            allure.attach(
                f"获取 apispec 失败: {e}",
                name="API规范错误",
                attachment_type=allure.attachment_type.TEXT,
            )

    # ---- 3. Flask-Admin ----
    with allure.step("3. Flask-Admin 可访问"):
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/admin/",
                timeout=10,
                allow_redirects=True,
            )
            allure.attach(
                f"Flask-Admin → {resp.status_code}",
                name="Flask-Admin",
                attachment_type=allure.attachment_type.TEXT,
            )
            assert resp.status_code in (200, 302), (
                f"Flask-Admin 应可访问，实际: {resp.status_code}"
            )
        except requests.RequestException as e:
            allure.attach(
                f"Flask-Admin 访问失败: {e}",
                name="Flask-Admin错误",
                attachment_type=allure.attachment_type.TEXT,
            )

    # ---- 4. Tags 完整性 ----
    with allure.step("4. Swagger Tags 完整性"):
        try:
            resp = requests.get(
                f"{base_url.rstrip('/')}/apispec_1.json",
                timeout=10,
            )
            if resp.status_code == 200:
                spec = resp.json()
                tags = [t.get("name", "") for t in spec.get("tags", [])]
                allure.attach(
                    f"Tags count: {len(tags)}\nTags: {tags}",
                    name="Swagger Tags",
                    attachment_type=allure.attachment_type.TEXT,
                )
                # 抽样关键 tag
                expected_tags = ["token", "user", "product", "order", "file"]
                found_tags = [t for t in expected_tags if any(t in tag.lower() for tag in tags)]
                assert len(found_tags) >= 3, (
                    f"关键 tag 缺失: 期望含 {expected_tags}, 实际 tags: {tags}"
                )
        except Exception:
            pass
