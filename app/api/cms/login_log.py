# _*_ coding: utf-8 _*_
"""
  Created by Allen7D on 2020/6/15.
  ↓↓↓ 登录日志接口 ↓↓↓
"""
from datetime import datetime

from flask import request

from app.extensions.api_docs.redprint import Redprint
from app.extensions.api_docs.cms import login_log as api_doc
from app.core.db import db
from app.core.token_auth import auth
from app.core.utils import paginate
from app.models.login_log import LoginLog
from app.dao.login_log import LoginLogDao
from app.libs.error_code import Success, ParameterException

__author__ = 'Allen7D'

api = Redprint(name='log/login', module='登录日志管理', api_doc=api_doc, alias='cms_login_log')


def _parse_login_time(value, field_name):
    if value in (None, ''):
        return None

    value = str(value).strip()
    if value.isdigit():
        if len(value) == 10:
            return int(value)
        if len(value) == 13:
            return int(value) // 1000
        raise ParameterException(msg=f'{field_name} 时间戳格式不正确')

    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return int(datetime.strptime(value, fmt).timestamp())
        except ValueError:
            continue
    raise ParameterException(msg=f'{field_name} 时间格式不正确')


@api.route('/list', methods=['GET'])
@api.route_meta(auth='查询登录日志列表', module='登录日志')
@api.doc(args=['g.query.page', 'g.query.size', 'g.query.start', 'g.query.end'], auth=True)
@auth.group_required
def get_log_list():
    '''查询登录日志列表'''
    page, size = paginate()
    start = _parse_login_time(request.args.get('start'), 'start')
    end = _parse_login_time(request.args.get('end'), 'end')
    paginator = LoginLogDao.get_log_list(page, size, start, end)
    return Success({
        'total': paginator.total,
        'current_page': paginator.page,
        'items': paginator.items
    })


def _parse_log_id(value):
    try:
        log_id = int(str(value).strip())
    except (TypeError, ValueError):
        raise ParameterException(msg='ID 必须为正整数')
    if log_id <= 0:
        raise ParameterException(msg='ID 必须为正整数')
    return log_id


@api.route('/<id>', methods=['GET'])
@api.route_meta(auth='查询登录日志', module='登录日志')
@api.doc(args=['g.path.log_id'], auth=True)
@auth.group_required
def get_log(id):
    '''查询登录日志'''
    log_id = _parse_log_id(id)
    log = LoginLog.get_or_404(id=log_id)
    return Success(log)


@api.route('/<id>', methods=['DELETE'])
@api.route_meta(auth='删除登录日志', module='登录日志')
@api.doc(args=['g.path.log_id'], auth=True)
@auth.admin_required
def delete_log(id):
    '''删除登录日志'''
    log_id = _parse_log_id(id)
    LoginLog.get_or_404(id=log_id).delete()
    return Success(error_code=2)


@api.route('/all', methods=['DELETE'])
@api.route_meta(auth='清除所有登录日志', module='登录日志')
@api.doc(auth=True)
@auth.admin_required
def delete_all_log():
    '''删除所有登录日志'''
    with db.auto_commit():
        LoginLog.query.filter().delete(synchronize_session=False)
    return Success(error_code=2)
