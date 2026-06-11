# _*_ coding: utf-8 _*_
"""
  Created by Allen7D on 2020/4/17.
"""
from sqlalchemy import func
from flask import current_app

from app.core.db import db
from app.libs.enums import AtLeastEnum, ClientTypeEnum
from app.models.identity import Identity
from app.libs.error_code import AtLeastOneClientException

__author__ = 'Allen7D'


class IdentityDao():
    # 绑定用户
    @staticmethod
    def bind(user_id, identifier, type):
        credential = None
        if ClientTypeEnum(type) in current_app.config['CLINET_INNER_TYPES']:
            credential = IdentityDao.get_credential(user_id=user_id)
        IdentityDao.create_identity(
            user_id=user_id,
            identifier=identifier,
            credential=credential,
            type=type)

    # 解绑用户
    @staticmethod
    def unbind(user_id, type):
        identity_count = db.session.query(func.count(Identity.user_id)).filter(
            Identity.user_id == user_id).scalar()
        # 至少保留一种登录方式
        if identity_count <= AtLeastEnum.ONE.value:
            raise AtLeastOneClientException()
        IdentityDao.delete_identity(user_id, type)

    # 新建身份
    @staticmethod
    def create_identity(user_id, identifier, credential, type):
        with db.auto_commit():
            Identity.create(commit=False, user_id=user_id, type=type,
                            identifier=identifier, credential=credential)

    # 更新身份
    @staticmethod
    def update_identity(commit=True, user_id=None, identifier=None, credential=None, type=None):
        identity = Identity.get(user_id=user_id, type=type)
        if identity:
            identity.update(commit=commit,
                            identifier=identifier, credential=credential)
        else:
            Identity.create(commit=commit, user_id=user_id, type=type,
                            identifier=identifier, credential=credential)

    # 删除身份
    @staticmethod
    def delete_identity(user_id, type):
        with db.auto_commit():
            identity = Identity.get_or_404(user_id=user_id, type=type)
            identity.hard_delete(commit=False)  # 硬删除

    # 获取加密后的密码
    @staticmethod
    def get_credential(user_id):
        result = db.session.query(Identity._credential).filter(
            Identity.user_id == user_id,
            Identity.type.in_([
                ClientTypeEnum.USERNAME.value,
                ClientTypeEnum.EMAIL.value,
                ClientTypeEnum.MOBILE.value]),
            Identity._credential != None
        ).first()
        return result[0] if result else None