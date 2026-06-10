# 登录与鉴权测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：令牌生成、令牌校验、受限接口访问、异常登录


| 用例编号        | 接口方法 | 接口路径               | 测试点      | 用例标题             | 前置条件         | 请求数据                                             | 预期结果               | 优先级 |
| ----------- | ---- | ------------------ | -------- | ---------------- | ------------ | ------------------------------------------------ | ------------------ | --- |
| TC-AUTH-001 | POST | `/v1/token`        | 正常登录     | 管理员账号登录成功        | 已导入测试数据      | `account=admin` `secret=admin123456` `type=100`  | 登录成功，返回 Token      | P0  |
| TC-AUTH-002 | POST | `/v1/token`        | 正常登录     | 普通用户 A 登录成功      | 已导入测试数据      | `account=alice` `secret=alice123456` `type=100`  | 登录成功，返回 Token      | P0  |
| TC-AUTH-003 | POST | `/v1/token`        | 正常登录     | 普通用户 B 登录成功      | 已导入测试数据      | `account=bob` `secret=bob123456` `type=100`      | 登录成功，返回 Token      | P0  |
| TC-AUTH-004 | POST | `/v1/token`        | 异常登录     | 密码错误登录失败         | 已导入测试数据      | `account=bob` `secret=wrong-password` `type=100` | 返回登录失败，不生成有效 Token | P0  |
| TC-AUTH-005 | POST | `/v1/token`        | 异常登录     | 不存在账号登录失败        | 已导入测试数据      | `account=ghost` `secret=123456` `type=100`       | 返回账号不存在或登录失败       | P0  |
| TC-AUTH-006 | POST | `/v1/token`        | 异常登录     | 空账号登录校验          | 已导入测试数据      | `account=""` `secret=123456` `type=100`          | 返回参数校验失败           | P0  |
| TC-AUTH-007 | POST | `/v1/token`        | 异常登录     | 空密码登录校验          | 已导入测试数据      | `account=admin` `secret=""` `type=100`           | 返回参数校验失败           | P0  |
| TC-AUTH-008 | POST | `/v1/token/verify` | Token 校验 | 未携带 Token 访问校验接口 | 已有受限接口       | `token` 为空                                       | 返回校验失败             | P0  |
| TC-AUTH-009 | POST | `/v1/token/verify` | Token 校验 | 伪造 Token 访问校验接口  | 已有受限接口       | `token=fake-token`                               | 返回鉴权失败             | P0  |
| TC-AUTH-010 | POST | `/v1/token/verify` | Token 校验 | 有效 Token 访问校验接口  | 已登录并获取 Token | `token=<valid-token>`                            | 接口正常返回解析结果         | P0  |


## 回归建议

- 登录失败类用例：`TC-AUTH-004` ~ `TC-AUTH-009`
- 核心冒烟：`TC-AUTH-001`、`TC-AUTH-002`、`TC-AUTH-008`、`TC-AUTH-010`

