# 权限分配管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：权限查询、按组查权限、新增/移除权限、删除组全部权限（`@auth.admin_required`）

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试 |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/auth/all` | GET | `@auth.admin_required` |
| `/cms/auth/by_group` | GET | `@auth.admin_required` |
| `/cms/auth/append` | PUT | `@auth.admin_required` |
| `/cms/auth/remove` | PUT | `@auth.admin_required` |
| `/cms/auth/by_group` | DELETE | `@auth.admin_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-PERM-001 | GET | `/cms/auth/all` | 权限查询 | 查询所有可分配权限成功 | 已登录管理员 | 无 | 返回权限列表，含 id、name、module | P0 |
| TC-PERM-002 | GET | `/cms/auth/by_group` | 按组查权限 | 查询指定权限组的权限列表成功 | 已登录管理员 | `group_id=1` | 返回该组权限列表 | P0 |
| TC-PERM-003 | GET | `/cms/auth/by_group` | 参数校验 | group_id 为空/不存在时查询 | 已登录管理员 | `group_id=`（不传）/ `group_id=9999` | 返回参数校验失败 / 返回空列表 | P1 |
| TC-PERM-004 | PUT | `/cms/auth/append` | 新增权限 | 为权限组新增多个权限成功 | 已登录管理员 | `group_id=2` `auth_ids=[10,11]` | 返回成功 error_code=1 | P0 |
| TC-PERM-005 | PUT | `/cms/auth/append` | 新增异常 | group_id 为空 / auth_ids 为空新增失败 | 已登录管理员 | `group_id=` / `auth_ids=[]` | 返回"请输入分组id" / "请输入auths字段" | P1 |
| TC-PERM-006 | PUT | `/cms/auth/remove` | 移除权限 | 从权限组移除多个权限成功 | 已登录管理员 | `group_id=2` `auth_ids=[10]`（刚追加的权限） | 返回成功 error_code=2 | P1 |
| TC-PERM-007 | DELETE | `/cms/auth/by_group` | 删除全部权限 | 删除某权限组的所有权限成功 | 已登录管理员 | `group_id=3`（非核心组） | 返回成功 error_code=2 | P1 |
| TC-PERM-008 | — | 全部 admin_required 接口 | 越权 | 普通用户访问权限接口被拒绝 | 已用 `user` 登录 | 以 GET `/cms/auth/all` 为例 | 返回权限不足错误 | P0 |
| TC-PERM-009 | — | 全部需登录接口 | 未登录 | 未登录访问权限接口被拒绝 | 未登录 | 以 GET `/cms/auth/all` 为例 | 返回未认证错误 | P1 |

## 回归建议

- 核心冒烟：`TC-PERM-001`、`TC-PERM-004`、`TC-PERM-008`
- 完整回归：全部 9 条
