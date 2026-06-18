# 参数配置管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：参数配置列表、按ID/Key查询、新建、更新、更新Value、删除  
> 鉴权：查询类只需登录，修改类需 `@auth.group_required`

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试（有 group_required 权限） |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/config/list` | GET | 需登录 |
| `/cms/config/{id}` | GET | 需登录 |
| `/cms/config/key/{key}` | GET | 需登录 |
| `/cms/config` | POST | `@auth.group_required` |
| `/cms/config/{id}` | PUT | `@auth.group_required` |
| `/cms/config/key/{key}` | PUT | `@auth.group_required` |
| `/cms/config/{id}` | DELETE | `@auth.group_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-CONFIG-001 | GET | `/cms/config/list` | 列表查询 | 分页查询参数配置列表成功 | 已登录 | `page=1` `size=10` | 返回分页列表，含 total、items | P0 |
| TC-CONFIG-002 | GET | `/cms/config/{id}` | 按ID查询 | 按ID查询参数成功；不存在失败 | 已登录 | `id=1` / `id=9999` | 返回参数详情 / 错误提示 | P1 |
| TC-CONFIG-003 | GET | `/cms/config/key/{key}` | 按Key查询 | 按Key查询参数成功；不存在失败 | 已登录 | `key=page_size` / `key=non_exist`（以实际数据为准） | 返回对应参数 / 错误提示 | P1 |
| TC-CONFIG-004 | POST | `/cms/config` | 新建 | 新建参数配置成功 | 已登录管理员 | `name=测试` `key=test_key` `value=v1` `type=true` | 返回成功 error_code=1 | P0 |
| TC-CONFIG-005 | POST | `/cms/config` | 新建异常 | 必填字段为空/重复key新建失败 | 已登录管理员 | `name=""` / `key=""` / 重复 `key=page_size` | 返回参数校验失败 / 数据重复 | P1 |
| TC-CONFIG-006 | PUT | `/cms/config/{id}` | 更新 | 更新参数配置成功 | 已登录管理员 | `id=2` `name=更新名` `value=new_val` | 返回成功 error_code=1 | P1 |
| TC-CONFIG-007 | PUT | `/cms/config/key/{key}` | 更新Value | 按Key更新value，更新后立即查询验证 | 已登录管理员 | 1. PUT `key=test_key value=new` 2. GET `key=test_key` | 返回成功，GET 验证 value 已变更 | P1 |
| TC-CONFIG-008 | DELETE | `/cms/config/{id}` | 删除 | 删除非核心参数成功；不存在失败 | 已登录管理员 | `id=3`（非核心）/ `id=9999` | 返回成功 error_code=2 / 错误提示 | P1 |
| TC-CONFIG-009 | — | group_required 接口 | 越权 | 普通用户访问修改类接口被拒 | 已用 `user` 登录 | 以 POST `/cms/config` 为例 | 返回权限不足错误 | P1 |
| TC-CONFIG-010 | — | 全部需登录接口 | 未登录 | 未登录访问参数接口被拒 | 未登录 | 以 GET `/cms/config/list` 为例 | 返回未认证错误 | P1 |

## 回归建议

- 核心冒烟：`TC-CONFIG-001`、`TC-CONFIG-004`、`TC-CONFIG-007`
- 完整回归：全部 10 条
