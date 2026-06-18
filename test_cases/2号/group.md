# 权限组管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：权限组 CRUD、用户迁移、权限校验（`@auth.admin_required`）

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试 |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/group/all` | GET | `@auth.admin_required` |
| `/cms/group/{id}` | GET | `@auth.admin_required` |
| `/cms/group` | POST | `@auth.admin_required` |
| `/cms/group/{id}` | PUT | `@auth.admin_required` |
| `/cms/group/{id}` | DELETE | `@auth.admin_required` |
| `/cms/group/migrate` | PUT | `@auth.admin_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-GROUP-001 | GET | `/cms/group/all` | 查询全部 | 查询所有权限组成功 | 已登录管理员 | 无 | 返回权限组列表，含 id、name、info | P0 |
| TC-GROUP-002 | GET | `/cms/group/{id}` | 查询单个 | 查询单个权限组及权限列表成功 | 已登录管理员 | `id=1` | 返回权限组详情，含 auth_list | P1 |
| TC-GROUP-003 | GET | `/cms/group/{id}` | 异常查询 | 查询不存在/非法ID的权限组失败 | 已登录管理员 | `id=9999`（不存在）/ `id=abc`（非法） | 返回"分组不存在" / 参数校验失败 | P1 |
| TC-GROUP-004 | POST | `/cms/group` | 新建 | 新建权限组成功 | 已登录管理员 | `name=测试分组` `info=测试描述` `auth_ids=[1,2]` | 返回成功 error_code=1 | P0 |
| TC-GROUP-005 | POST | `/cms/group` | 新建异常 | 名称为空/重复名称新建失败 | 已登录管理员 | `name=""`（空）/ `name=超级管理员组`（重复） | 返回"请输入分组名称" / 数据重复 | P1 |
| TC-GROUP-006 | PUT | `/cms/group/{id}` | 更新 | 更新权限组名称和描述成功 | 已登录管理员 | `id=2` `name=更新后组名` `info=更新描述` | 返回成功 error_code=1 | P1 |
| TC-GROUP-007 | DELETE | `/cms/group/{id}` | 删除 | 删除无用户的权限组成功；删除不存在组失败 | 已登录管理员 | `id=3`（正常）/ `id=9999`（不存在） | 返回成功 error_code=2 / "分组不存在" | P1 |
| TC-GROUP-008 | PUT | `/cms/group/migrate` | 迁移 | 迁移权限组下用户成功；相同 src/dest 失败 | 已登录管理员 | `src_id=2` `dest_id=3`（正常）/ `src=2 dest=2`（相同） | 返回成功 / "src_id与dest_id不能相同" | P2 |
| TC-GROUP-009 | — | 全部 admin_required 接口 | 越权 | 普通用户访问权限组接口被拒绝 | 已用 `user` 登录 | 以任意上述接口为例（如 GET `/cms/group/all`） | 返回权限不足错误 | P0 |
| TC-GROUP-010 | — | 全部需登录接口 | 未登录 | 未登录访问权限组接口被拒绝 | 未登录 | 以任意上述接口为例（如 GET `/cms/group/all`） | 返回未认证错误 | P1 |

## 回归建议

- 核心冒烟：`TC-GROUP-001`、`TC-GROUP-004`、`TC-GROUP-009`
- 完整回归：全部 10 条
