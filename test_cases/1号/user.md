# 用户接口测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：用户信息查询、权限查询、资料修改、头像修改、密码修改、账号绑定解绑、注销


| 用例编号        | 接口方法   | 接口路径                | 测试点  | 用例标题                 | 前置条件                | 请求数据                                                                                                | 预期结果                         | 优先级 |
| ----------- | ------ | ------------------- | ---- | -------------------- | ------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------- | --- |
| TC-USER-001 | GET    | `/v1/user`          | 用户信息 | 查询当前登录用户信息及字段完整性     | 已登录                 | Header：`Authorization: Bearer <valid-token>`                                                        | 返回当前用户信息正确，包含昵称、权限组、头像等字段    | P0  |
| TC-USER-002 | GET    | `/v1/user`          | 登录态  | 未携带 Token 查询当前用户失败   | 无                   | 不携带 Token                                                                                           | 返回token无效                    | P0  |
| TC-USER-003 | GET    | `/v1/user/auths`    | 权限查询 | 普通管理员查询自身权限成功        | 已用 `admin` 登录       | Header：`Authorization` 携带 admin Token                                                               | 返回权限列表                       | P1  |
| TC-USER-004 | GET    | `/v1/user/auths`    | 权限查询 | 未分配权限组的普通用户查询权限返回空列表 | 已用 `user` 登录        | Header：`Authorization` 携带 user Token                                                                | 返回 `{"items": []}`           | P1  |
| TC-USER-005 | PUT    | `/v1/user/avatar`   | 头像修改 | 更新用户头像               | 已登录                 | `avatar=http://abc/xzy.jpg`                                                                         | 头像更新成功                       | P1  |
| TC-USER-006 | PUT    | `/v1/user/password` | 密码修改 | 修改当前用户密码成功           | 已登录                 | `old_password=123456` `new_password=1234567` `confirm_password=1234567`                             | 修改成功，数据库密码已更新，新密码可登录、旧密码不可登录 | P0  |
| TC-USER-007 | PUT    | `/v1/user/password` | 密码修改 | 旧密码错误修改失败            | 已登录                 | `old_password=wrong-password` `new_password=1234567` `confirm_password=1234567`                     | 返回密码错误，不更新数据库密码              | P0  |
| TC-USER-008 | PUT    | `/v1/user/password` | 参数校验 | 新密码长度 5 位校验失败        | 已登录                 | `old_password=123456` `new_password=12345` `confirm_password=12345`                                 | 返回密码长度校验失败                   | P1  |
| TC-USER-009 | PUT    | `/v1/user/password` | 参数校验 | 新密码长度 6 位校验通过        | 已登录                 | `old_password=123456` `new_password=123456` `confirm_password=123456`                               | 修改成功                         | P1  |
| TC-USER-010 | PUT    | `/v1/user/password` | 参数校验 | 新密码长度 22 位校验通过       | 已登录                 | `old_password=123456` `new_password=Abc123_Abc123_Abc123` `confirm_password=Abc123_Abc123_Abc123`   | 修改成功                         | P2  |
| TC-USER-011 | PUT    | `/v1/user/password` | 参数校验 | 新密码长度 23 位校验失败       | 已登录                 | `old_password=123456` `new_password=Abc123_Abc123_Abc1234` `confirm_password=Abc123_Abc123_Abc1234` | 返回密码长度校验失败                   | P1  |
| TC-USER-012 | PUT    | `/v1/user/password` | 参数校验 | 新密码包含非法字符校验失败        | 已登录                 | `old_password=123456` `new_password=1234567!` `confirm_password=1234567!`                           | 返回密码字符规则校验失败                 | P1  |
| TC-USER-013 | PUT    | `/v1/user/password` | 参数校验 | 两次输入的新密码不一致校验失败      | 已登录                 | `old_password=123456` `new_password=1234567` `confirm_password=7654321`                             | 返回两次输入的密码不一致，不更新数据库密码        | P1  |
| TC-USER-014 | PUT    | `/v1/user`          | 资料修改 | 更新当前用户资料             | 已登录                 | `username=Allen7D` `nickname=Allen7D` `mobile=13758787058` `email=462870781@qq.com`                 | 资料更新成功                       | P1  |
| TC-USER-015 | PUT    | `/v1/user`          | 资料修改 | 同时提交原用户名、原手机号、原邮箱成功  | 已用 `user` 登录        | `username=user` `mobile=19900000003` `email=111@qq.com` `nickname=普通用户`                             | 更新成功，不触发服务器端异常               | P1  |
| TC-USER-016 | PUT    | `/v1/user`          | 重复校验 | 更新为其他用户已占用用户名失败      | 已用 `user` 登录        | `username=admin`                                                                                    | 返回该用户名已被使用                   | P1  |
| TC-USER-017 | PUT    | `/v1/user`          | 重复校验 | 更新为其他用户已占用手机号失败      | 已用 `user` 登录        | `mobile=19900000002`                                                                                | 返回手机号已被使用                    | P1  |
| TC-USER-018 | PUT    | `/v1/user`          | 重复校验 | 更新为其他用户已占用邮箱失败       | 已用 `user` 登录        | `email=777@qq.com`                                                                                  | 返回邮箱已被使用                     | P1  |
| TC-USER-019 | PUT    | `/v1/user/bind`     | 账号绑定 | 绑定未占用邮箱成功            | 已登录且已解绑邮箱           | `account=new_user_email@qq.com` `type=101`                                                          | 绑定成功                         | P1  |
| TC-USER-020 | PUT    | `/v1/user/bind`     | 账号绑定 | 已绑定邮箱时再次绑定邮箱失败       | 已用 `user` 登录且已绑定邮箱  | `account=another_email@qq.com` `type=101`                                                           | 返回当前用户已绑定邮箱，不新增多条邮箱身份        | P1  |
| TC-USER-021 | PUT    | `/v1/user/bind`     | 账号绑定 | 已绑定手机号时再次绑定手机号失败     | 已用 `user` 登录且已绑定手机号 | `account=19900000009` `type=102`                                                                    | 返回当前用户已绑定手机号，不新增多条手机号身份      | P1  |
| TC-USER-022 | PUT    | `/v1/user/bind`     | 账号绑定 | 绑定其他用户已占用邮箱失败        | 已用 `user` 登录        | `account=777@qq.com` `type=101`                                                                     | 返回邮箱已被使用，不返回服务器端异常           | P1  |
| TC-USER-023 | PUT    | `/v1/user/bind`     | 账号绑定 | 绑定其他用户已占用手机号失败       | 已用 `user` 登录        | `account=19900000002` `type=102`                                                                    | 返回手机号已被使用，不返回服务器端异常          | P1  |
| TC-USER-024 | PUT    | `/v1/user/unbind`   | 账号解绑 | 解绑绑定账号               | 已登录                 | `type=101`                                                                                          | 解绑成功                         | P1  |
| TC-USER-025 | PUT    | `/v1/user/unbind`   | 账号解绑 | 解绑不存在的账号             | 已登录                 | `type=101`                                                                                          | 解绑失败返回未查询到数据                 | P1  |
| TC-USER-026 | DELETE | `/v1/user`          | 注销账号 | 注销当前账号               | 已登录                 | 无                                                                                                   | 注销成功或返回确认结果                  | P2  |
| TC-USER-027 | POST   | `/v1/user`          | 注册恢复 | 用户名+手机号匹配已删除账号时复用    | 存在已删除账号且用户名、手机号均同名  | `nickname="普通用户"` `username="user"` `mobile=19900000003` `email=new@qq.com`                         | 复用已删除账号，补充邮箱/更新信息            | P1  |
| TC-USER-028 | POST   | `/v1/user`          | 注册恢复 | 用户名+邮箱匹配已删除账号时复用     | 存在已删除账号且用户名、邮箱均同名   | `nickname="普通用户"` `username="user"` `mobile=10000000000` `email=111@qq.com`                         | 复用已删除账号，补充手机号/更新信息           | P1  |


## 回归建议

- 核心冒烟：`TC-USER-001`、`TC-USER-002`、`TC-USER-003`、`TC-USER-006`
- 权限查询：`TC-USER-003`、`TC-USER-004`
- 密码修改：`TC-USER-006` ~ `TC-USER-013`
- 用户资料：`TC-USER-005`、`TC-USER-014` ~ `TC-USER-018`
- 绑定解绑：`TC-USER-019` ~ `TC-USER-025`

