# -*- coding: utf-8 -*-
"""
单元测试: app/core/auth.py
U-07: get_ep_name      — 通过 ID 查询 endpoint 名称
U-08: find_auth_module — 通过权限名查找 meta 信息
U-09: is_in_auth_scope — 判断权限范围
"""
import pytest
from collections import namedtuple
from unittest.mock import patch

from app.core.error import NotFound


# ──────────────────────────────────────────────
# U-07: get_ep_name
# ──────────────────────────────────────────────
class TestGetEpName:
    """U-07: 通过 ID 查询 endpoint 名称"""

    def test_existing_id(self, app, app_context):
        """存在的 ID 返回名称"""
        app.config['EP_INFO_LIST'] = [
            {'id': 1, 'name': '商品管理'},
            {'id': 2, 'name': '用户管理'},
            {'id': 3, 'name': '订单管理'},
        ]
        from app.core.auth import get_ep_name
        assert get_ep_name(1) == '商品管理'
        assert get_ep_name(2) == '用户管理'
        assert get_ep_name(3) == '订单管理'

    def test_non_existing_id(self, app, app_context):
        """不存在的 ID 抛 NotFound 异常"""
        app.config['EP_INFO_LIST'] = [
            {'id': 1, 'name': '商品管理'},
        ]
        from app.core.auth import get_ep_name
        with pytest.raises(NotFound) as exc_info:
            get_ep_name(999)
        assert '999' in exc_info.value.msg

    def test_empty_list(self, app, app_context):
        """空列表 — 任何 ID 都抛 NotFound"""
        app.config['EP_INFO_LIST'] = []
        from app.core.auth import get_ep_name
        with pytest.raises(NotFound):
            get_ep_name(1)

    def test_single_element(self, app, app_context):
        """仅一个元素时的边界情况"""
        app.config['EP_INFO_LIST'] = [{'id': 1, 'name': '测试'}]
        from app.core.auth import get_ep_name
        assert get_ep_name(1) == '测试'


# ──────────────────────────────────────────────
# U-08: find_auth_module
# ──────────────────────────────────────────────
class TestFindAuthModule:
    """U-08: 通过权限名查找 meta 信息"""

    @pytest.fixture
    def setup_ep_meta(self, app):
        """设置测试用 EP_META 配置"""
        Meta = namedtuple('Meta', ['name', 'module'])
        app.config['EP_META'] = {
            'endpoint_add_product': Meta('新增商品', '商品'),
            'endpoint_edit_product': Meta('编辑商品', '商品'),
            'endpoint_view_user': Meta('查看用户', '用户'),
            'endpoint_delete_user': Meta('删除用户', '用户'),
        }
        return app

    def test_existing_module(self, app, setup_ep_meta, app_context):
        """存在的权限名返回对应 meta"""
        from app.core.auth import find_auth_module
        result = find_auth_module('新增商品')
        assert result is not None
        assert result.name == '新增商品'
        assert result.module == '商品'

    def test_existing_another_module(self, app, setup_ep_meta, app_context):
        """另一模块的权限名"""
        from app.core.auth import find_auth_module
        result = find_auth_module('查看用户')
        assert result is not None
        assert result.name == '查看用户'
        assert result.module == '用户'

    def test_non_existing_name(self, app, setup_ep_meta, app_context):
        """不存在的权限名返回 None"""
        from app.core.auth import find_auth_module
        result = find_auth_module('不存在的权限')
        assert result is None

    def test_empty_ep_meta(self, app, app_context):
        """空 EP_META — 任何名称都返回 None"""
        app.config['EP_META'] = {}
        from app.core.auth import find_auth_module
        result = find_auth_module('随便什么名字')
        assert result is None

    def test_name_not_in_meta(self, app, setup_ep_meta, app_context):
        """EP_META 中有数据但不包含目标名称"""
        from app.core.auth import find_auth_module
        result = find_auth_module('系统设置')  # 不在清单中
        assert result is None


# ──────────────────────────────────────────────
# U-09: is_in_auth_scope
# ──────────────────────────────────────────────
class TestIsInAuthScope:
    """U-09: 判断 group_id 是否在权限范围内"""

    @pytest.fixture
    def setup_ep_meta(self, app):
        """设置 EP_META: 一个管理类 endpoint"""
        Meta = namedtuple('Meta', ['name', 'module'])
        app.config['EP_META'] = {
            'admin.dashboard': Meta('查看仪表盘', '系统管理'),
        }
        return app

    def test_meta_exists_and_auth_match(self, app, setup_ep_meta, app_context):
        """meta 存在且权限匹配 → 返回 True"""
        from app.core.auth import is_in_auth_scope
        with patch('app.core.auth.Auth') as MockAuth:
            MockAuth.get.return_value = True  # 模拟数据库中权限记录存在
            result = is_in_auth_scope(group_id=1, endpoint='admin.dashboard')
            assert result is True

    def test_meta_exists_but_auth_not_match(self, app, setup_ep_meta, app_context):
        """meta 存在但权限不匹配 → 返回 False"""
        from app.core.auth import is_in_auth_scope
        with patch('app.core.auth.Auth') as MockAuth:
            MockAuth.get.return_value = False  # 模拟数据库中无权限记录(返回 None/False)
            result = is_in_auth_scope(group_id=2, endpoint='admin.dashboard')
            assert result is False

    def test_meta_exists_auth_returns_none(self, app, setup_ep_meta, app_context):
        """Auth.get 返回 None → 视为 False"""
        from app.core.auth import is_in_auth_scope
        with patch('app.core.auth.Auth') as MockAuth:
            MockAuth.get.return_value = None
            result = is_in_auth_scope(group_id=3, endpoint='admin.dashboard')
            assert result is False

    def test_meta_not_exists(self, app, app_context):
        """meta 不存在 → 预期 AttributeError(代码缺陷: print 在 None 上调用 .name)"""
        app.config['EP_META'] = {}
        from app.core.auth import is_in_auth_scope
        with patch('app.core.auth.Auth') as MockAuth:
            # 即使 mock 了 Auth，meta 为 None 时 print(meta.name) 仍会出错
            with pytest.raises(AttributeError):
                is_in_auth_scope(group_id=1, endpoint='nonexistent.endpoint')
