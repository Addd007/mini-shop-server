# -*- coding: utf-8 -*-
"""
单元测试: app/core/utils.py
U-06: as_namedtuple   — 字典转 namedtuple
U-10: get_request_args — 获取请求参数合并
"""
import json
import pytest
from collections import namedtuple

from app.core.utils import as_namedtuple, get_request_args


class TestAsNamedtuple:
    """U-06: 字典转 namedtuple"""

    def test_normal_dict(self):
        """普通字典转换"""
        result = as_namedtuple({'name': 'test', 'age': 18})
        assert result.name == 'test'
        assert result.age == 18

    def test_empty_dict(self):
        """空字典转换"""
        result = as_namedtuple({})
        # 空 namedtuple — 无字段
        assert result._fields == ()

    def test_skip_none_values(self):
        """包含 None 值的字段被跳过"""
        result = as_namedtuple({'a': 1, 'b': None, 'c': 3, 'd': None})
        # b 和 d 应为 None，被跳过
        assert hasattr(result, 'a')
        assert hasattr(result, 'c')
        assert not hasattr(result, 'b')
        assert not hasattr(result, 'd')
        assert result.a == 1
        assert result.c == 3

    def test_all_none_values(self):
        """全部为 None — 返回空 namedtuple"""
        result = as_namedtuple({'x': None, 'y': None})
        assert result._fields == ()

    def test_string_keys(self):
        """字符串 key 字典"""
        result = as_namedtuple({'first_name': 'John', 'last_name': 'Doe'})
        assert result.first_name == 'John'
        assert result.last_name == 'Doe'

    def test_mixed_types(self):
        """混合类型字典"""
        data = {'int_val': 1, 'str_val': 'hello', 'list_val': [1, 2, 3], 'bool_val': True}
        result = as_namedtuple(data)
        assert result.int_val == 1
        assert result.str_val == 'hello'
        assert result.list_val == [1, 2, 3]
        assert result.bool_val is True


class TestGetRequestArgs:
    """U-10: 获取请求参数"""

    def test_body_and_query_merge(self, app):
        """body + query 参数合并 — 返回 namedtuple（默认）"""
        with app.test_request_context(
            '/test?page=1&size=10',
            data=json.dumps({'keyword': 'hello'}),
            content_type='application/json'
        ):
            result = get_request_args()
            assert hasattr(result, 'page')
            assert hasattr(result, 'size')
            assert hasattr(result, 'keyword')
            assert result.page == '1'
            assert result.size == '10'
            assert result.keyword == 'hello'

    def test_body_only(self, app):
        """仅有 body 参数"""
        with app.test_request_context(
            '/test',
            data=json.dumps({'username': 'admin', 'action': 'create'}),
            content_type='application/json'
        ):
            result = get_request_args()
            assert hasattr(result, 'username')
            assert hasattr(result, 'action')
            assert result.username == 'admin'
            assert result.action == 'create'

    def test_query_only(self, app):
        """仅有 query 参数"""
        with app.test_request_context(
            '/items?category=books&sort=price'
        ):
            result = get_request_args()
            assert hasattr(result, 'category')
            assert hasattr(result, 'sort')
            assert result.category == 'books'
            assert result.sort == 'price'

    def test_return_as_dict(self, app):
        """as_dict=True 返回字典"""
        with app.test_request_context(
            '/test?key=value',
            data=json.dumps({'data': 123}),
            content_type='application/json'
        ):
            result = get_request_args(as_dict=True)
            assert isinstance(result, dict)
            assert result['key'] == 'value'
            assert result['data'] == 123

    def test_skip_none_values_in_args(self, app):
        """参数中 None 值被跳过"""
        with app.test_request_context(
            '/test?page=1',
            data=json.dumps({'a': 1, 'b': None}),
            content_type='application/json'
        ):
            # b=None 应该被过滤掉
            result = get_request_args()
            assert hasattr(result, 'page')
            assert hasattr(result, 'a')
            # b 不应出现在结果中
            assert not hasattr(result, 'b')

    def test_no_query_no_body(self, app):
        """无 query 也无 body — 返回空 namedtuple"""
        with app.test_request_context('/empty'):
            result = get_request_args()
            assert result._fields == ()

    def test_query_override_body(self, app):
        """query 参数覆盖同名 body 参数（dict 合并行为: query 后传入覆盖）"""
        with app.test_request_context(
            '/test?name=query_name',
            data=json.dumps({'name': 'body_name', 'other': 'val'}),
            content_type='application/json'
        ):
            result = get_request_args()
            # dict(data, **args): args(query) 覆盖 data(body)
            assert result.name == 'query_name'
            assert result.other == 'val'
