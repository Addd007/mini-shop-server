# _*_ coding: utf-8 _*_
"""
  Created by Allen7D on 2020/4/16.
"""
from app.core.db import db
from app.libs.enums import ScopeEnum, ClientTypeEnum
from app.libs.error_code import AuthFailed, UserException, RepeatException
from app.models.user import User
from app.models.identity import Identity
from app.dao.identity import IdentityDao

__author__ = 'Allen7D'


class UserDao():
    # 更改密码
    @staticmethod
    def change_password(uid, old_password, new_password):
        identity_list = Identity.query.filter(
            Identity.type.in_([
                ClientTypeEnum.USERNAME.value,
                ClientTypeEnum.EMAIL.value,
                ClientTypeEnum.MOBILE.value]),
            Identity.user_id == uid
        ).all()
        if not identity_list:
            raise UserException(msg='当前用户没有可修改密码的登录方式')

        password_identities = [item for item in identity_list if item.password]
        if not password_identities:
            raise UserException(msg='当前用户没有可修改密码的登录方式')
        if not any(item.check_password(old_password) for item in password_identities):
            raise AuthFailed(msg='密码错误')

        with db.auto_commit():
            for item in identity_list:
                item.update(commit=False, password=new_password)

    # 重置密码
    @staticmethod
    def reset_password(uid, password):
        identity_list = Identity.query.filter(
            Identity.type.in_([
                ClientTypeEnum.USERNAME.value,
                ClientTypeEnum.EMAIL.value,
                ClientTypeEnum.MOBILE.value]),
            Identity.user_id == uid
        ).all()
        with db.auto_commit():
            for item in identity_list:
                item.update(commit=False, password=password)

    # 站内注册(用户名、手机号、邮箱、密码)
    @staticmethod
    def create_user(form):
        def _has(attr):
            return hasattr(form, attr) and getattr(form, attr) is not None

        def _find_deleted_identity(identity_type, identifier):
            if identifier is None:
                return None
            return db.session.query(Identity).filter(
                Identity.type == identity_type,
                Identity.identifier == identifier,
                Identity.delete_time != None
            ).first()

        def _find_active_identity(identifier):
            return db.session.query(Identity).filter(
                Identity.identifier == identifier,
                Identity.delete_time == None
            ).first()

        with db.auto_commit():
            username = getattr(form, 'username', None) if _has('username') else None
            mobile = getattr(form, 'mobile', None) if _has('mobile') else None
            email = getattr(form, 'email', None) if _has('email') else None
            nickname = getattr(form, 'nickname', None)

            reuse_user = None
            username_identity = _find_deleted_identity(ClientTypeEnum.USERNAME.value, username) if username else None
            mobile_identity = _find_deleted_identity(ClientTypeEnum.MOBILE.value, mobile) if mobile else None
            email_identity = _find_deleted_identity(ClientTypeEnum.EMAIL.value, email) if email else None

            # 复用条件：用户名 + 手机号 / 用户名 + 邮箱 / 用户名 + 手机号 + 邮箱
            # 只要能命中同一个软删除账号，并且该账号没有被其他活跃 identity 占用，就允许复用并补全缺失信息
            candidate_user_ids = []
            if username_identity and mobile_identity and username_identity.user_id == mobile_identity.user_id:
                candidate_user_ids.append(username_identity.user_id)
            if username_identity and email_identity and username_identity.user_id == email_identity.user_id:
                candidate_user_ids.append(username_identity.user_id)

            if candidate_user_ids:
                candidate_user_id = candidate_user_ids[0]
                if (not mobile_identity or mobile_identity.user_id == candidate_user_id) and \
                   (not email_identity or email_identity.user_id == candidate_user_id):
                    reuse_user = User.query.filter(
                        User.id == candidate_user_id,
                        User.delete_time != None
                    ).first()

            if reuse_user:
                reuse_user.delete_time = None
                reuse_user.nickname = nickname or reuse_user.nickname
                reuse_user.auth = ScopeEnum.COMMON.value

                current_identities = db.session.query(Identity).filter(Identity.user_id == reuse_user.id).all()
                identity_map = {item.type: item for item in current_identities}
                password = form.password

                for identity_type, identifier, verified in [
                    (ClientTypeEnum.USERNAME.value, username, 1),
                    (ClientTypeEnum.MOBILE.value, mobile, 0),
                    (ClientTypeEnum.EMAIL.value, email, 0),
                ]:
                    if identifier is None:
                        continue
                    active_conflict = _find_active_identity(identifier)
                    if active_conflict and active_conflict.user_id != reuse_user.id:
                        raise RepeatException(msg='该账号已被使用，请重新输入新的账号')

                    identity = identity_map.get(identity_type)
                    if identity:
                        identity.delete_time = None
                        identity.update(commit=False, identifier=identifier, password=password)
                    else:
                        Identity.create(commit=False, user_id=reuse_user.id, type=identity_type,
                                        verified=verified, identifier=identifier, password=password)
                return reuse_user

            user = User.create(
                commit=False,
                nickname=nickname,
                auth=ScopeEnum.COMMON.value
            )
            if _has('username'):
                Identity.abort_repeat(identifier=form.username, msg='该用户名已被使用，请重新输入新的用户名')
                Identity.create(commit=False, user_id=user.id, type=ClientTypeEnum.USERNAME.value, verified=1,
                                identifier=form.username, password=form.password)
            if _has('mobile'):
                Identity.abort_repeat(identifier=form.mobile, msg='手机号已被使用，请重新输入新的手机号')
                Identity.create(commit=False, user_id=user.id, type=ClientTypeEnum.MOBILE.value,
                                identifier=form.mobile, password=form.password)
            if _has('email'):
                Identity.abort_repeat(identifier=form.email, msg='邮箱已被使用，请重新输入新的邮箱号')
                Identity.create(commit=False, user_id=user.id, type=ClientTypeEnum.EMAIL.value,
                                identifier=form.email, password=form.password)

    @staticmethod
    def register_by_wx_mina(openid: str):
        """小程序注册"""
        with db.auto_commit():
            user = User.create(commit=False)
            Identity.create(
                commit=False, user_id=user.id,
                type=ClientTypeEnum.WX_MINA.value,
                identifier=openid, verified=1
            )
        return user

    @staticmethod
    def register_by_wx_open(form):
        """微信第三方注册
        :param form: 属性包含(openid、unionid、nickname、headimgurl)
        """
        return User.create(**form)

    @staticmethod
    def register_by_wx_account():
        pass

    # 更新用户
    @staticmethod
    def update_user(uid, form):
        # 第1步: 核对需修改的信息(用户名、手机号、邮箱)
        identity_infos = []
        if (hasattr(form, 'username')):
            identity_infos.append(
                {'identifier': form.username, 'type': ClientTypeEnum.USERNAME.value, 'msg': '该用户名已被使用，请重新输入新的用户名'})
        if (hasattr(form, 'mobile')):
            identity_infos.append(
                {'identifier': form.mobile, 'type': ClientTypeEnum.MOBILE.value, 'msg': '手机号已被使用，请重新输入新的手机号'})
        if (hasattr(form, 'email')):
            identity_infos.append(
                {'identifier': form.email, 'type': ClientTypeEnum.EMAIL.value, 'msg': '邮箱已被使用，请重新输入新的邮箱号'})
        # 第2步: 修改用户信息
        with db.auto_commit():
            # 第2.1步: 获取用户信息
            user = User.query.filter_by(id=uid).first_or_404()
            credential = IdentityDao.get_credential(user_id=uid)
            # 第2.2步: 先校验身份标识是否被其他身份占用
            for item in identity_infos:
                current_identity = db.session.query(Identity).filter(
                    Identity.user_id == uid,
                    Identity.type == item['type'],
                    Identity.delete_time == None
                ).first()
                existed_identity = db.session.query(Identity).filter(
                    Identity.identifier == item['identifier']
                ).first()
                if existed_identity and (not current_identity or existed_identity.id != current_identity.id):
                    raise RepeatException(msg=item['msg'])
                item['current_identity'] = current_identity
            # 第2.3步: 修改用户昵称
            if hasattr(form, 'nickname'):
                user.update(commit=False, nickname=form.nickname)
            # 第2.4步: 依次修改用户身份信息(用户名、手机号、邮箱)
            for item in identity_infos:
                current_identity = item['current_identity']
                if current_identity:
                    current_identity.update(commit=False, identifier=item['identifier'], credential=credential)
                else:
                    Identity.create(commit=False, user_id=uid, type=item['type'],
                                    identifier=item['identifier'], credential=credential)

    # 更新头像
    @staticmethod
    def set_avatar(id, avatar):
        '''
        :param id: 用户id
        :param avatar: 头像url
        :return:
        '''
        with db.auto_commit():
            user = User.get(id=id)
            user._avatar = avatar

    # 删除用户
    @staticmethod
    def delete_user(uid):
        user = User.query.filter_by(id=uid).first_or_404()
        identity_list = Identity.query.filter_by(user_id=user.id).all()
        with db.auto_commit():
            for identity in identity_list:
                identity.delete(commit=False)
            user.delete(commit=False)

    # 更换权限组
    @staticmethod
    def change_group(uid, group_id):
        user = User.get_or_404(id=uid)
        user.update(group_id=group_id)

    # 获取用户列表
    @staticmethod
    def get_user_list(page, size):
        paginator = User.query \
            .filter_by(auth=ScopeEnum.COMMON.value) \
            .paginate(page=page, per_page=size, error_out=True)
        paginator.hide('address')
        return {
            'total': paginator.total,
            'current_page': paginator.page,
            'items': paginator.items
        }
