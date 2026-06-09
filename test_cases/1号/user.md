# 用户与权限测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：当前用户信息、权限边界、停用账号、个人资料修改、账号绑定

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-USER-001 | GET | `/v1/user` | 用户信息 | 查询当前登录用户信息 | 已登录 | Header：`Authorization: Bearer <valid-token>` | 返回当前用户信息正确 | P0 |
| TC-USER-002 | GET | `/v1/user` | 用户信息 | 用户信息字段完整性 | 已登录 | 任意有效 Token | 返回昵称、权限组、头像、备注等字段 | P1 |
| TC-USER-003 | POST | `/v1/token` | 账号状态 | 停用账号不允许登录 | 已导入测试数据 | `account=test_disabled` `secret=123456` `type=100` | 登录失败，状态校验生效 | P0 |
| TC-USER-004 | GET | `/v1/user/auths` | 权限查询 | 查询自己拥有的权限 | 已登录 admin | Header：`Authorization: Bearer <admin-token>` | 返回当前用户拥有的权限列表 | P0 |
| TC-USER-005 | PUT | `/v1/user/avatar` | 头像修改 | 更新用户头像 | 已登录 | `avatar=http://abc/xzy.jpg` | 头像更新成功 | P1 |
| TC-USER-006 | PUT | `/v1/user/password` | 密码修改 | 修改当前用户密码 | 已登录 | `old_password=123456` `new_password=123456` `confirm_password=123456` | 修改成功 | P1 |
| TC-USER-007 | PUT | `/v1/user` | 资料修改 | 更新当前用户资料 | 已登录 | `username=Allen7D` `nickname=Allen7D` `mobile=13758787058` `email=462870781@qq.com` | 资料更新成功 | P1 |
| TC-USER-008 | PUT | `/v1/user/bind` | 账号绑定 | 绑定邮箱或微信账号 | 已登录 | `account=999@qq.com` `type=101` | 绑定成功 | P1 |
| TC-USER-009 | PUT | `/v1/user/unbind` | 账号解绑 | 解绑绑定账号 | 已登录 | `type=101` | 解绑成功 | P1 |
| TC-USER-010 | DELETE | `/v1/user` | 注销账号 | 注销当前账号 | 已登录 | 无 | 注销成功或返回确认结果 | P2 |

## 回归建议

- 核心冒烟：`TC-USER-001`、`TC-USER-003`、`TC-USER-004`
- 用户资料：`TC-USER-005`、`TC-USER-006`、`TC-USER-007`
- 绑定解绑：`TC-USER-008`、`TC-USER-009`
