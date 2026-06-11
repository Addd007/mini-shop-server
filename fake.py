# _*_ coding: utf-8 _*_
"""
  Created by Allen7D on 2018/5/12.
"""
from app import create_app
from app.core.db import db
from app.libs.enums import ClientTypeEnum, ScopeEnum
from app.models.identity import Identity
from app.models.user import User

__author__ = 'Allen7D'


def get_user_by_identifier(identifier):
    identity = Identity.get(identifier=identifier)
    return User.query.get(identity.user_id) if identity else None


def save_identity(user_id, identity_type, identifier, password=None, credential=None):
    identity = Identity.get(type=identity_type, identifier=identifier)
    if identity is None:
        identity = Identity()
        identity.user_id = user_id
        identity.type = identity_type
        identity.identifier = identifier
        db.session.add(identity)
    else:
        identity.user_id = user_id

    if password is not None:
        identity.password = password
    if credential is not None:
        identity.credential = credential

    return identity


def create_user(nickname, auth, username, email, mobile, openid, password):
    user = get_user_by_identifier(username) \
        or get_user_by_identifier(email) \
        or get_user_by_identifier(mobile) \
        or get_user_by_identifier(openid)

    if user is None:
        user = User()
        db.session.add(user)
        db.session.flush()

    user.nickname = nickname
    user.auth = auth

    save_identity(user.id, ClientTypeEnum.USERNAME.value, username, password=password)
    save_identity(user.id, ClientTypeEnum.EMAIL.value, email, password=password)
    save_identity(user.id, ClientTypeEnum.MOBILE.value, mobile, password=password)
    save_identity(user.id, ClientTypeEnum.WX_MINA.value, openid, credential='')

    return user


app = create_app()
with app.app_context():
    with db.auto_commit():
        create_user(
            nickname='超级管理员',
            auth=ScopeEnum.ADMIN.value,
            username='super',
            email='999@qq.com',
            mobile='19900000001',
            openid='999',
            password='123456'
        )
        create_user(
            nickname='普通管理员',
            auth=ScopeEnum.COMMON.value,
            username='admin',
            email='777@qq.com',
            mobile='19900000002',
            openid='777',
            password='123456'
        )
        create_user(
            nickname='普通用户',
            auth=ScopeEnum.COMMON.value,
            username='user',
            email='111@qq.com',
            mobile='19900000003',
            openid='111',
            password='123456'
        )

