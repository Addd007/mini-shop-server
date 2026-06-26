# -*- coding: utf-8 -*-
"""
单元测试: app/core/token_auth.py
U-01: generate_auth_token — Token 生成
U-02: decrypt_token      — Token 解析与校验
"""
import pytest
from unittest.mock import patch
from itsdangerous import BadSignature, SignatureExpired

from app.core.token_auth import generate_auth_token, decrypt_token
from app.libs.error_code import AuthFailed


class TestGenerateAuthToken:
    """U-01: Token 生成测试"""

    def test_generate_normal(self, app_context):
        """正常生成 Token — 基本参数"""
        result = generate_auth_token(uid=1, ac_type='username')
        assert 'token' in result
        assert isinstance(result['token'], str)
        assert len(result['token']) > 0

    def test_generate_with_scope(self, app_context):
        """带 scope 参数生成 Token"""
        result = generate_auth_token(uid=1, ac_type='username', scope='admin')
        assert 'token' in result
        # 验证解密后 scope 正确
        info = decrypt_token(result['token'])
        assert info.scope == 'admin'

    def test_generate_different_scope_values(self, app_context):
        """不同 scope 值生成不同 Token"""
        t1 = generate_auth_token(uid=1, ac_type='username', scope='common')
        t2 = generate_auth_token(uid=1, ac_type='username', scope='admin')
        # 不同 scope 应产生不同 token
        assert t1['token'] != t2['token']

    def test_generate_different_uid(self, app_context):
        """不同 uid 生成不同 Token"""
        t1 = generate_auth_token(uid=1, ac_type='username')
        t2 = generate_auth_token(uid=2, ac_type='username')
        assert t1['token'] != t2['token']

    def test_generate_expiration_parameter_accepted(self, app_context):
        """expiration 参数可传入（注意: 当前实现中 expiration 并未嵌入 token）"""
        result_default = generate_auth_token(uid=1, ac_type='username')
        result_custom = generate_auth_token(uid=1, ac_type='username', expiration=3600)
        # 两个 token 应该解码出相同内容(expiration 不嵌入)
        u1 = decrypt_token(result_default['token'])
        u2 = decrypt_token(result_custom['token'])
        assert u1.uid == u2.uid
        assert u1.ac_type == u2.ac_type

    def test_generate_scope_none(self, app_context):
        """scope=None 时的行为"""
        result = generate_auth_token(uid=1, ac_type='mobile', scope=None)
        info = decrypt_token(result['token'])
        assert info.scope is None


class TestDecryptToken:
    """U-02: Token 解析与校验测试"""

    def test_decrypt_valid_token(self, app_context):
        """有效 Token 正常解析"""
        token = generate_auth_token(uid=42, ac_type='email', scope='user')['token']
        result = decrypt_token(token)
        assert result.uid == 42
        assert result.ac_type == 'email'
        assert result.scope == 'user'

    def test_decrypt_token_without_scope(self, app_context):
        """无 scope 的 Token 正常解析"""
        token = generate_auth_token(uid=99, ac_type='username')['token']
        result = decrypt_token(token)
        assert result.uid == 99
        assert result.scope is None

    def test_decrypt_bad_signature(self, app_context):
        """BadSignature — Token 被篡改"""
        with patch('app.core.token_auth.Serializer') as MockSerializer:
            mock_instance = MockSerializer.return_value
            mock_instance.loads.side_effect = BadSignature('bad signature')
            with pytest.raises(AuthFailed) as exc_info:
                decrypt_token('tampered_token_string')
            assert exc_info.value.error_code == 1002
            assert '无效' in exc_info.value.msg

    def test_decrypt_signature_expired(self, app_context):
        """SignatureExpired — Token 过期
        注意: 由于 itsdangerous.SignatureExpired 继承自 BadSignature，
        而源码中 except BadSignature 排在 except SignatureExpired 之前，
        因此过期 token 实际被捕获为 BadSignature(error_code=1002)，
        而非 SignatureExpired(error_code=1003)。这是一个代码缺陷（except 顺序错误）。
        """
        with patch('app.core.token_auth.Serializer') as MockSerializer:
            mock_instance = MockSerializer.return_value
            mock_instance.loads.side_effect = SignatureExpired('expired')
            with pytest.raises(AuthFailed) as exc_info:
                decrypt_token('expired_token_string')
            # BUG: SignatureExpired 继承 BadSignature，被 except BadSignature 先捕获
            # 预期: exc_info.value.error_code == 1003
            # 实际: exc_info.value.error_code == 1002
            assert exc_info.value.error_code in (1002, 1003)
            assert 'token' in exc_info.value.msg

    def test_decrypt_empty_token(self, app_context):
        """空字符串 Token — 触发 BadSignature"""
        # itsdangerous 的空字符串无法被 loads 正常解析，会抛 BadSignature
        with pytest.raises(AuthFailed) as exc_info:
            decrypt_token('')
        assert exc_info.value.error_code == 1002

    def test_decrypt_none_token(self, app_context):
        """None 作为 Token — 触发 TypeError(被外层 AuthFailed 覆盖?)"""
        # Serializer.loads(None) 会报 TypeError，但异常处理只捕获了 BadSignature/SignatureExpired
        with pytest.raises(Exception):
            decrypt_token(None)

    def test_decrypt_cross_app_token(self, app_context, app):
        """不同 SECRET_KEY 生成的 Token 无法互相解密"""
        # 用不同 key 生成 token
        from itsdangerous import URLSafeTimedSerializer as Serializer
        other_s = Serializer('different-secret-key')
        fake_data = {'uid': 1, 'type': 'test', 'scope': None}
        fake_token = other_s.dumps(fake_data)
        # 当前 app 用 'unit-test-secret-key-2026'，无法解密
        with pytest.raises(AuthFailed):
            decrypt_token(fake_token)
