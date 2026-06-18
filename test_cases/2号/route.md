# 路由管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：路由树查询、路由节点 CRUD（部分接口 `@auth.admin_required`）

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试 |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/route/tree` | GET | 需登录 |
| `/cms/route/tree/with_element` | GET | 需登录 |
| `/cms/route/tree` | PUT | `@auth.admin_required` |
| `/cms/route/{id}` | GET | `@auth.admin_required` |
| `/cms/route/{id}` | PUT | 需登录 |
| `/cms/route/{id}` | DELETE | `@auth.admin_required` |
| `/cms/route` | POST | `@auth.admin_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-ROUTE-001 | GET | `/cms/route/tree` | 路由树 | 获取所有路由树结构成功 | 已登录 | 无 | 返回嵌套路由树，含 id、title、children | P0 |
| TC-ROUTE-002 | GET | `/cms/route/tree/with_element` | 路由树(含元素) | 获取路由树含页面元素成功 | 已登录 | 无 | 返回路由树，节点额外包含 element 信息 | P1 |
| TC-ROUTE-003 | GET | `/cms/route/{id}` | 路由节点 | 按ID查询路由节点成功；不存在/非法ID失败 | 已登录管理员 | `id=1`（正常）/ `id=9999` / `id=abc` | 返回路由节点详情 / "路由节点不存在" / 参数校验失败 | P1 |
| TC-ROUTE-004 | POST | `/cms/route` | 新增节点 | 新增路由节点成功 | 已登录管理员 | `parent_id=0` `title=测试` `name=test` `icon=test` `path=/test` `component=Test` | 返回成功含新建节点信息 | P1 |
| TC-ROUTE-005 | POST | `/cms/route` | 新增异常 | 必填字段（title/name）为空新增失败 | 已登录管理员 | `title=""` / `name=""` | 返回参数校验失败 | P1 |
| TC-ROUTE-006 | PUT | `/cms/route/{id}` | 修改节点 | 按ID修改路由节点成功 | 已登录 | `id=2` `title=修改后` `name=updated` | 返回成功 | P1 |
| TC-ROUTE-007 | DELETE | `/cms/route/{id}` | 删除节点 | 删除叶子路由节点成功；不存在失败 | 已登录管理员 | `id=10`（叶子节点）/ `id=9999` | 返回成功 / 错误提示 | P1 |
| TC-ROUTE-008 | — | admin_required 接口 | 越权 | 普通用户访问管理员专属路由接口被拒 | 已用 `user` 登录 | 以 GET `/cms/route/1` 为例 | 返回权限不足错误 | P1 |
| TC-ROUTE-009 | — | 全部需登录接口 | 未登录 | 未登录访问路由接口被拒 | 未登录 | 以 GET `/cms/route/tree` 为例 | 返回未认证错误 | P1 |

## 回归建议

- 核心冒烟：`TC-ROUTE-001`、`TC-ROUTE-004`、`TC-ROUTE-006`
- 完整回归：全部 9 条
