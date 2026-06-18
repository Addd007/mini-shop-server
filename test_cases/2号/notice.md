# 通知公告管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：通知列表、详情（公开）、新建、更新、批量删除  
> 鉴权：详情接口公开；其余需 `@auth.group_required`

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试（有 group_required 权限） |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/notice/list` | GET | `@auth.group_required` |
| `/cms/notice/{id}` | GET | **公开**（无需登录） |
| `/cms/notice` | POST | `@auth.group_required` |
| `/cms/notice/{id}` | PUT | `@auth.group_required` |
| `/cms/notice/{ids}` | DELETE | `@auth.group_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-NOTICE-001 | GET | `/cms/notice/list` | 列表查询 | 分页查询通知列表成功 | 已登录管理员 | `page=1` `size=10` | 返回通知分页列表 | P0 |
| TC-NOTICE-002 | GET | `/cms/notice/{id}` | 公开详情 | 查询通知详情成功（公开接口，无需登录也可访问） | 无需登录 | `id=1` | 返回通知详情，含 title、content、status | P0 |
| TC-NOTICE-003 | GET | `/cms/notice/{id}` | 异常查询 | 查询不存在的通知失败 | 无需登录 | `id=9999` | 返回对应错误提示 | P1 |
| TC-NOTICE-004 | POST | `/cms/notice` | 新建 | 新建通知成功（含发布/草稿两种状态） | 已登录管理员 | `type=1` `title=测试` `content=内容` （`status=true`发布 / `status=false`草稿） | 返回成功 error_code=1 | P0 |
| TC-NOTICE-005 | POST | `/cms/notice` | 新建异常 | title/content为空新建失败 | 已登录管理员 | `title=""` / `content=""` | 返回参数校验失败 | P1 |
| TC-NOTICE-006 | PUT | `/cms/notice/{id}` | 更新 | 更新通知成功（如将草稿改为发布） | 已登录管理员 | `id=2` `title=更新` `status=true` | 返回成功 error_code=1 | P1 |
| TC-NOTICE-007 | DELETE | `/cms/notice/{ids}` | 删除 | 单条/批量删除通知成功；ids非法失败 | 已登录管理员 | `ids=3`（单条）/ `ids=4,5`（批量）/ `ids=abc`（非法） | 返回成功 error_code=2 / 参数校验失败 | P1 |
| TC-NOTICE-008 | — | 公开 vs 受限 | 权限对比 | 普通用户可访问公开详情，但列表/新建/删除被拒；未登录仅可访问详情 | 已用 `user` 登录 / 未登录 | GET `/cms/notice/1`（均可） vs GET `/cms/notice/list`（被拒） | 公开接口正常；受限接口返回权限不足/未认证 | P1 |

## 回归建议

- 核心冒烟：`TC-NOTICE-001`、`TC-NOTICE-002`、`TC-NOTICE-004`
- 完整回归：全部 8 条
