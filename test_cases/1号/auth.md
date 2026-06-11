# 登录与鉴权测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：令牌生成、令牌校验、用户名登录、邮箱登录、手机号登录、异常登录

## 测试账号说明

测试账号由 `fake.py` 初始化：


| 角色    | 用户名     | 邮箱           | 手机号           | 密码       | 登录类型          |
| ----- | ------- | ------------ | ------------- | -------- | ------------- |
| 超级管理员 | `super` | `999@qq.com` | `19900000001` | `123456` | `100/101/102` |
| 普通管理员 | `admin` | `777@qq.com` | `19900000002` | `123456` | `100/101/102` |
| 普通用户  | `user`  | `111@qq.com` | `19900000003` | `123456` | `100/101/102` |


登录类型说明：


| type  | 含义    |
| ----- | ----- |
| `100` | 用户名登录 |
| `101` | 邮箱登录  |
| `102` | 手机号登录 |



| 用例编号        | 接口方法 | 接口路径               | 测试点    | 用例标题          | 前置条件          | 请求数据                                              | 预期结果               | 优先级 |
| ----------- | ---- | ------------------ | ------ | ------------- | ------------- | ------------------------------------------------- | ------------------ | --- |
| TC-AUTH-001 | POST | `/v1/token`        | 用户名登录  | 超级管理员用户名登录成功  | 已执行 `fake.py` | `account=super` `secret=123456` `type=100`        | 登录成功，返回 Token      | P0  |
| TC-AUTH-002 | POST | `/v1/token`        | 用户名登录  | 普通管理员用户名登录成功  | 已执行 `fake.py` | `account=admin` `secret=123456` `type=100`        | 登录成功，返回 Token      | P0  |
| TC-AUTH-003 | POST | `/v1/token`        | 用户名登录  | 普通用户用户名登录成功   | 已执行 `fake.py` | `account=user` `secret=123456` `type=100`         | 登录成功，返回 Token      | P0  |
| TC-AUTH-004 | POST | `/v1/token`        | 邮箱登录   | 超级管理员邮箱登录成功   | 已执行 `fake.py` | `account=999@qq.com` `secret=123456` `type=101`   | 登录成功，返回 Token      | P0  |
| TC-AUTH-005 | POST | `/v1/token`        | 邮箱登录   | 普通管理员邮箱登录成功   | 已执行 `fake.py` | `account=777@qq.com` `secret=123456` `type=101`   | 登录成功，返回 Token      | P1  |
| TC-AUTH-006 | POST | `/v1/token`        | 邮箱登录   | 普通用户邮箱登录成功    | 已执行 `fake.py` | `account=111@qq.com` `secret=123456` `type=101`   | 登录成功，返回 Token      | P1  |
| TC-AUTH-007 | POST | `/v1/token`        | 邮箱登录   | 邮箱大小写混合登录成功   | 已执行 `fake.py` | `account=999@Qq.CoM` `secret=123456` `type=101`   | 登录成功，返回 Token      | P2  |
| TC-AUTH-008 | POST | `/v1/token`        | 手机号登录  | 超级管理员手机号登录成功  | 已执行 `fake.py` | `account=19900000001` `secret=123456` `type=102`  | 登录成功，返回 Token      | P0  |
| TC-AUTH-009 | POST | `/v1/token`        | 手机号登录  | 普通管理员手机号登录成功  | 已执行 `fake.py` | `account=19900000002` `secret=123456` `type=102`  | 登录成功，返回 Token      | P1  |
| TC-AUTH-010 | POST | `/v1/token`        | 手机号登录  | 普通用户手机号登录成功   | 已执行 `fake.py` | `account=19900000003` `secret=123456` `type=102`  | 登录成功，返回 Token      | P1  |
| TC-AUTH-011 | POST | `/v1/token`        | 异常登录   | 密码错误登录失败      | 已执行 `fake.py` | `account=user` `secret=wrong-password` `type=100` | 返回密码错误，不生成有效 Token | P0  |
| TC-AUTH-012 | POST | `/v1/token`        | 异常登录   | 用户名不存在登录失败    | 已执行 `fake.py` | `account=ghost` `secret=123456` `type=100`        | 返回用户名未注册或登录失败      | P0  |
| TC-AUTH-013 | POST | `/v1/token`        | 异常登录   | 邮箱不存在登录失败     | 已执行 `fake.py` | `account=ghost@qq.com` `secret=123456` `type=101` | 返回邮箱未注册或登录失败       | P1  |
| TC-AUTH-014 | POST | `/v1/token`        | 异常登录   | 手机号不存在登录失败    | 已执行 `fake.py` | `account=19999999999` `secret=123456` `type=102`  | 返回手机号未注册或登录失败      | P1  |
| TC-AUTH-015 | POST | `/v1/token`        | 异常登录   | 登录类型无效        | 已执行 `fake.py` | `account=user` `secret=123456` `type=999`         | 返回登录方式无效或参数校验失败    | P0  |
| TC-AUTH-016 | POST | `/v1/token`        | 异常登录   | 用户名大小写不匹配登录失败 | 已执行 `fake.py` | `account=Super` `secret=123456` `type=100`        | 返回用户名未注册，不应忽略大小写   | P2  |
| TC-AUTH-017 | POST | `/v1/token`        | 异常登录   | 停用账号不允许登录     | 已导入测试数据       | `account=test_disabled` `secret=123456` `type=100` | 登录失败，状态校验生效        | P0  |
| TC-AUTH-018 | POST | `/v1/token`        | 参数校验   | 空账号登录校验       | 已执行 `fake.py` | `account=""` `secret=123456` `type=100`           | 返回账户不为空或参数校验失败     | P0  |
| TC-AUTH-019 | POST | `/v1/token`        | 参数校验   | 空密码登录校验       | 已执行 `fake.py` | `account=user` `secret=""` `type=100`             | 返回密码错误，不生成有效 Token | P0  |
| TC-AUTH-020 | POST | `/v1/token`        | 参数校验   | 缺少登录类型        | 已执行 `fake.py` | `account=user` `secret=123456` 缺少 `type`          | 返回参数校验失败           | P0  |
| TC-AUTH-021 | POST | `/v1/token/verify` | Token 校验 | 未携带 Token 访问校验接口 | 无         | `token` 为空                                        | 返回校验失败             | P0  |
| TC-AUTH-022 | POST | `/v1/token/verify` | Token 校验 | 伪造 Token 访问校验接口  | 无         | `token=fake-token`                                | 返回token失效          | P0  |
| TC-AUTH-023 | POST | `/v1/token/verify` | Token 校验 | 有效 Token 访问校验接口  | 已登录并获取 Token | `token=<valid-token>`                             | 接口正常返回解析结果         | P0  |


## 回归建议

- 核心冒烟：`TC-AUTH-001`、`TC-AUTH-004`、`TC-AUTH-008`、`TC-AUTH-023`
- 登录方式覆盖：`TC-AUTH-001` ~ `TC-AUTH-010`
- 登录失败类用例：`TC-AUTH-011` ~ `TC-AUTH-017`
- 参数校验：`TC-AUTH-018` ~ `TC-AUTH-020`
- Token 校验：`TC-AUTH-021` ~ `TC-AUTH-023`
