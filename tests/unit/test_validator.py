# -*- coding: utf-8 -*-
"""
单元测试: app/core/validator.py
U-03: isPositiveInteger — 正整数校验
U-04: isNaturalNumber  — 自然数校验
U-05: isList / isEmptyList — 列表校验
"""
import pytest
from app.core.validator import PropVelifyMixin


class TestValidator:
    """验证器测试套件"""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.mixin = PropVelifyMixin()

    # ===========================
    # U-03: isPositiveInteger
    # ===========================
    @pytest.mark.parametrize('value,expected', [
        (1, True),           # 正整数
        (100, True),         # 较大正整数
        ('42', True),        # 字符串形式的正整数 → int转换后仍然>0
        ('0', False),        # 字符串0 → int(0), 不大于0
        (0, False),          # 零
        (-1, False),         # 负数
        (-100, False),       # 较大负数
        ('abc', False),      # 非数字字符串 → ValueError
        (None, False),       # None → int(None) 报 TypeError
        (1.5, True),         # 正浮点数 → int(1.5)=1, >0
        (0.0, False),        # 零浮点数 → int(0.0)=0
        ('', False),         # 空字符串 → int('') 报 ValueError
        (True, True),        # bool True → int(True)=1, >0
        (False, False),      # bool False → int(False)=0
    ])
    def test_is_positive_integer(self, value, expected):
        """U-03: 测试 isPositiveInteger 覆盖各类输入"""
        if value is None:
            # int(None) → TypeError，函数没 catch TypeError
            with pytest.raises(TypeError):
                self.mixin.isPositiveInteger(value)
        elif value == '':
            # int('') → ValueError → catch → return False
            result = self.mixin.isPositiveInteger(value)
            assert result is expected
        else:
            result = self.mixin.isPositiveInteger(value)
            assert result is expected

    # ===========================
    # U-04: isNaturalNumber
    # ===========================
    @pytest.mark.parametrize('value,expected', [
        (0, True),           # 自然数包含0
        (10, True),          # 正整数也是自然数
        ('3', True),         # 可转为自然数的字符串
        ('0', True),         # 字符串0 → int 0，>=0
        (-1, False),         # 负数
        (-99, False),        # 较大负数
        ('abc', False),      # 非数字
        (None, False),       # None
        (5.0, True),         # 正浮点 → int(5.0)=5
        (-0.5, True),        # int(-0.5)=0，仍>=0 (注意: -0.5取整为0)
        ('', False),         # 空字符串 → ValueError
    ])
    def test_is_natural_number(self, value, expected):
        """U-04: 测试 isNaturalNumber 覆盖各类输入"""
        if value is None:
            with pytest.raises(TypeError):
                self.mixin.isNaturalNumber(value)
        elif value == '':
            result = self.mixin.isNaturalNumber(value)
            assert result is expected
        else:
            result = self.mixin.isNaturalNumber(value)
            assert result is expected

    # ===========================
    # U-05: isList
    # ===========================
    @pytest.mark.parametrize('value,expected', [
        ([1, 2, 3], True),   # 标准列表
        ([], True),          # 空列表(仍是列表类型)
        (list(), True),      # 显式 list()
        ((), False),         # 元组 → 不是 list
        ({}, False),         # 字典 → 不是 list
        ('abc', False),      # 字符串 → 不是 list
        (42, False),         # 整数 → 不是 list
        (None, False),       # None → 不是 list
        (set(), False),      # 集合 → 不是 list
    ])
    def test_is_list(self, value, expected):
        """U-05: 测试 isList 类型判断"""
        assert self.mixin.isList(value) is expected

    # ===========================
    # U-05: isEmptyList
    # ===========================
    @pytest.mark.parametrize('value,expected', [
        ([], True),                     # 空列表
        ([1, 2, 3], False),             # 非空列表
        ((), False),                    # 空元组(非列表类型)
        ('', False),                    # 空字符串(非列表类型)
        (None, False),                  # None
        ({}, False),                    # 空字典
    ])
    def test_is_empty_list(self, value, expected):
        """U-05: 测试 isEmptyList 空列表判断"""
        assert self.mixin.isEmptyList(value) is expected
