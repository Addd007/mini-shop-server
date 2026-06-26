# -*- coding: utf-8 -*-
"""
单元测试公共 fixture
为 app/core/ 的函数提供 Flask app context 基础设施
"""
import pytest
from flask import Flask


@pytest.fixture(scope='function')
def app():
    """创建最小配置的 Flask 测试应用，不连接数据库"""
    app = Flask(__name__)
    app.config.update({
        'SECRET_KEY': 'unit-test-secret-key-2026',
        'DEBUG': False,
        'EP_META': {},
        'EP_INFO_LIST': [],
        'EP_INFOS': {},
        'PAGE_DEFAULT': 1,
        'SIZE_DEFAULT': 10,
    })
    return app


@pytest.fixture(scope='function')
def app_context(app):
    """提供 Flask 应用上下文"""
    with app.app_context():
        yield
