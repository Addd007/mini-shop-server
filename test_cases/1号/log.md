# 日志测试用例

> 责任人：1号  
> 测试基线：`/apispec_1.json`  
> 覆盖范围：登录日志、操作日志、日志列表查询、日志删除

| 用例编号 | 接口方法 | 接口路径 | 测试点 | 用例标题 | 前置条件 | 请求数据 | 预期结果 | 优先级 |
|---|---|---|---|---|---|---|---|---|
| TC-LOG-001 | GET | `/cms/log/login/list` | 登录日志 | 查询登录日志列表成功 | 已登录管理员 | `page=1` `size=10` `start` `end` | 返回登录日志分页列表 | P1 |
| TC-LOG-002 | GET | `/cms/log/login/{id}` | 登录日志详情 | 查询单条登录日志成功 | 已登录管理员 | `id=1` | 返回登录日志详情 | P1 |
| TC-LOG-003 | DELETE | `/cms/log/login/{id}` | 删除日志 | 删除登录日志成功 | 已登录管理员 | `id=1` | 删除成功 | P2 |
| TC-LOG-004 | DELETE | `/cms/log/login/all` | 清空日志 | 删除所有登录日志成功 | 已登录管理员 | 无 | 清空成功 | P2 |
| TC-LOG-005 | GET | `/cms/log/oper/list/search` | 操作日志搜索 | 按人员/时间/内容搜索操作日志 | 已登录管理员 | `page=1` `size=10` `start` `end` `username=Allen7D` `keyword=测试` | 返回操作日志搜索结果 | P1 |
| TC-LOG-006 | GET | `/cms/log/oper/user/list` | 用户列表日志 | 查询操作日志中的用户列表成功 | 已登录管理员 | `page=1` `size=10` | 返回用户列表日志 | P1 |
| TC-LOG-007 | GET | `/cms/log/oper/{id}` | 操作日志详情 | 查询单条操作日志成功 | 已登录管理员 | `id=1` | 返回操作日志详情 | P1 |
| TC-LOG-008 | DELETE | `/cms/log/oper/{id}` | 删除日志 | 删除操作日志成功 | 已登录管理员 | `id=1` | 删除成功 | P2 |
| TC-LOG-009 | DELETE | `/cms/log/oper/all` | 清空日志 | 删除所有操作日志成功 | 已登录管理员 | 无 | 清空成功 | P2 |

## 回归建议

- 核心查询：`TC-LOG-001`、`TC-LOG-002`、`TC-LOG-005`、`TC-LOG-006`、`TC-LOG-007`
- 清理类：`TC-LOG-003`、`TC-LOG-004`、`TC-LOG-008`、`TC-LOG-009`
