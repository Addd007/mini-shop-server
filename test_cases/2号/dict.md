# 字典管理测试用例

> 责任人：2号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：字典数据查询（按type分页/全部/详情）、新建、更新、删除  
> 鉴权：全部需要 `@auth.group_required`

## 测试账号

| 角色 | 用户名 | 密码 | 用途 |
|------|--------|------|------|
| 超级管理员 | `super` | `123456` | 正向测试（有 group_required 权限） |
| 普通用户 | `user` | `123456` | 越权测试 |

## 接口清单

| 接口 | 方法 | 鉴权 |
|------|------|------|
| `/cms/dict/list` | GET | `@auth.group_required` |
| `/cms/dict/all` | GET | `@auth.group_required` |
| `/cms/dict/{id}` | GET | `@auth.group_required` |
| `/cms/dict` | POST | `@auth.group_required` |
| `/cms/dict/{id}` | PUT | `@auth.group_required` |
| `/cms/dict/{id}` | DELETE | `@auth.group_required` |

---

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-DICT-001 | GET | `/cms/dict/list` | 分页查询 | 按type分页查询字典列表成功 | 已登录管理员 | `type=gender` `page=1` `size=10`（type以实际数据为准） | 返回分页列表，含 total、items | P0 |
| TC-DICT-002 | GET | `/cms/dict/all` | 全量查询 | 按type查询某类全部字典数据成功 | 已登录管理员 | `type=status` | 返回该type下所有字典项 | P1 |
| TC-DICT-003 | GET | `/cms/dict/{id}` | 详情查询 | 查询单条字典成功；不存在失败 | 已登录管理员 | `id=1` / `id=9999` | 返回字典详情 / 错误提示 | P1 |
| TC-DICT-004 | GET | `/cms/dict/list` | 边界 | type为空/不存在时查询 | 已登录管理员 | `type=`（不传）/ `type=non_exist` | 参数校验失败 / 返回空列表 | P1 |
| TC-DICT-005 | POST | `/cms/dict` | 新建 | 新建字典数据成功 | 已登录管理员 | `order=1` `label=测试` `value=test` `type=gender` | 返回成功 error_code=1 | P0 |
| TC-DICT-006 | POST | `/cms/dict` | 新建异常 | label/value/type为空新建失败 | 已登录管理员 | `label=""` / `value=""` / `type=""` | 返回参数校验失败 | P1 |
| TC-DICT-007 | PUT | `/cms/dict/{id}` | 更新 | 更新字典数据成功（含部分字段更新） | 已登录管理员 | `id=2` `label=更新标签` / 仅 `status=false` | 返回成功，字段正确更新 | P1 |
| TC-DICT-008 | DELETE | `/cms/dict/{id}` | 删除 | 删除字典数据成功；不存在失败 | 已登录管理员 | `id=5`（非核心）/ `id=9999` | 返回成功 error_code=2 / 错误提示 | P1 |
| TC-DICT-009 | — | 全部 group_required 接口 | 越权+未登录 | 普通用户/未登录访问字典接口被拒 | 已用 `user` 登录 / 未登录 | 以 GET `/cms/dict/all?type=gender` 为例 | 返回权限不足 / 未认证错误 | P1 |

## 回归建议

- 核心冒烟：`TC-DICT-001`、`TC-DICT-005`、`TC-DICT-009`
- 完整回归：全部 9 条
